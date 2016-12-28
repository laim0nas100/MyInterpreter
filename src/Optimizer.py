import sys

from src.LexNames import LexName
from src.SpecificTypes import Tnames, Scope
from src.TAC import TACgen
from src.lib import ArrayList, OrderedMap


class Optimizer:
    scopes = OrderedMap()
    output = False

    @staticmethod
    def debugPrint(*args,**kwargs):
        if Optimizer.output:
            print(*args, **kwargs)

    @staticmethod
    def optimizeDeadCodeBlock(block:Scope):
        foundJumpOrReturn = False
        i = -1
        while True:
            i+=1
            if i>=block.statements.size():
                break
            st = block.statements[i]

            if not foundJumpOrReturn:
                if st.operation in [Tnames.JUMP, Tnames.RETURN]:
                    foundJumpOrReturn = True
                    continue
            if foundJumpOrReturn:
                if st.operation != Tnames.LABEL:
                    block.statements.pop(i)
                    i-=1
                else:
                    foundJumpOrReturn = False


    @staticmethod
    def optimizeEmptyJumps(block:Scope):
        i = 0
        while True:
            i += 1
            if i >= block.statements.size():
                break
            s1 = block.statements[i-1]
            s2 = block.statements[i]
            if s1.operation in [Tnames.JUMP,Tnames.JUMPZ]:
                if s2.operation == Tnames.LABEL:
                    if s1.tuple[1] == s2.tuple[1]:
                        block.statements.pop(i-1)
                        block.statements.pop(i-1)
                        i-=2
        return block


    @staticmethod
    def optimizeUnusedLabels(block:Scope,usedLabels:list):
        i = -1
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            if st.operation == Tnames.LABEL:
                if st.tuple[1] not in usedLabels:
                    block.statements.pop(i)
                    i-=1
        return block

    @staticmethod
    def getUsedLabels(t:TACgen):
        usedLabels = list()
        for block in t.scopes.returnItemsInOrder():
            for st in block.statements:
                if st.operation in [Tnames.JUMP,Tnames.JUMPZ]:
                    usedLabels.append(st.tuple[1])
        return usedLabels

    @staticmethod
    def optimizeEmptyExpressions(block:Scope):
        i = -1
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]


            if st.operation == Tnames.BEGINEXP:
                popped = ArrayList(None, None)
                block.statements.pop(i)
                while True:
                    popped.append(block.statements.pop(i))
                    st = block.statements[i]
                    if st.operation == Tnames.ENDEXP:
                        block.statements.pop(i)
                        st = block.statements[i]
                        if st.operation == Tnames.JUMPZ:
                            # expression value is used in "IF" statement so return everything except tags
                            block.statements.extendAt(popped,i)
                        break
                i-=1
        return block


    @staticmethod
    def optimizeEmptyBlocks(t:TACgen):
        pass

    @staticmethod
    def optimizeDeadCode(t:TACgen):
        for block in t.scopes.returnItemsInOrder():
            Optimizer.optimizeDeadCodeBlock(block)
            Optimizer.optimizeEmptyJumps(block)
            Optimizer.optimizeEmptyExpressions(block)
        usedLabels = Optimizer.getUsedLabels(t)
        # print(usedLabels)
        for block in t.scopes.returnItemsInOrder():
            Optimizer.optimizeUnusedLabels(block, usedLabels)
        return t


    @staticmethod
    def variableIsUsedInScope(scope:Scope,variableName:str):
        for st in scope.statements:
            if st.operation == Tnames.LOAD:
                if st.tuple[2] == variableName:
                    return True
            elif st.operation == Tnames.LOADARR:
                if st.tuple[2][0] == variableName:
                    return True
        return False


    @staticmethod
    def variableIsUsed(varName,definedIn:str,startAt:Scope):
        while True:
            if startAt is None:
                return False
            if Optimizer.variableIsUsedInScope(startAt,varName):
                return True
            else:
                if definedIn == startAt.getParentLabel():
                    return Optimizer.variableIsUsedInScope(Optimizer.scopes.get(definedIn),varName)
                else:
                    startAt = Optimizer.scopes.get(startAt.getParentLabel())

    @staticmethod
    def variablesAreUsedAtAll(t:TACgen)->ArrayList:
        results = ArrayList(None,None)
        scopeArray = ArrayList(t.scopes.returnItemsInOrder(), None)
        for scope in scopeArray:
            for var in scope.variables.keyOrder:
                for scopeInner in scopeArray:
                    if scope.label in scopeInner.label:
                        if (scope.label == scopeInner.label) or (not scopeInner.variables.containsKey(var) and scope.label != scopeInner.label):
                            used = Optimizer.variableIsUsed(var,scope.label,scopeInner)
                            if used:
                                Optimizer.debugPrint(var,"from",scope.label, "is used in", scopeInner.label)
                            else:
                                Optimizer.debugPrint(var, "from", scope.label, "is not used in", scopeInner.label)
                            results.append([var,scope.label,used])
        i = 0
        while True:
            i += 1
            if i>=len(results):
                break
            if (results[i-1][0] == results[i][0])and(results[i-1][1] == results[i][1])and(results[i-1][2] == results[i][2]):
                results.pop(i)
                i-=1

        return results

    @staticmethod
    def optimizeUnusedVariables(t:TACgen):
        iteration = 1
        info = Optimizer.variablesAreUsedAtAll(t)
        l = len(info)

        while True:
            Optimizer.debugPrint("iteration", iteration)
            iteration+=1
            var = info.getLast()
            while True:
                if info.size()==0:
                    break
                varName = var[0]
                varLabel = var[1]
                notUsedLabels = []
                used = False
                while True:
                    if info.size() == 0:
                        break
                    inf = info.getLast()
                    Optimizer.debugPrint("analise",var,inf)
                    if varName == inf[0] and varLabel == inf[1]:
                        if inf[2]:
                            Optimizer.debugPrint("Used")
                            used = True
                        else:
                            pass
                            notUsedLabels.append(varLabel)
                            Optimizer.debugPrint("Not used")
                    else:
                        Optimizer.debugPrint("New analise")
                        var = info.getLast()
                        break
                    info.pop()
                # remove if not used
                if not used:
                    scope = t.scopes.get(varLabel)
                    Optimizer.removeVariableInit(varName,scope)
                    for label in notUsedLabels:
                        scope = t.scopes.get(label)
                        Optimizer.removeVariableModify(varName,scope)
            info = Optimizer.variablesAreUsedAtAll(t)
            if l == len(info):
                break
            else:
                l = len(info)

    @staticmethod
    def removeVariableInit(varName,block:Scope):
        i = -1
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            popCount = 0
            if st.operation == Tnames.BEGININIT:
                popIndex = i
                while True:
                    popCount += 1
                    st = block.statements[i]
                    if st.operation == Tnames.ENDINIT:
                        if block.statements[i-1].tuple[1][1] == varName:
                            Optimizer.debugPrint("Removed init operations",varName,"at",block.label)
                            while popCount>0:
                                block.statements.pop(popIndex)
                                popCount-=1
                            i = popIndex-1
                            block.variables.removeByKey(varName)
                        break
                    i += 1
        return block

    @staticmethod
    def removeVariableModify(varName,block:Scope):
        i = -1
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            popCount = 0
            if st.operation == Tnames.BEGINMODIFY:
                popIndex = i
                while True:
                    popCount += 1
                    st = block.statements[i]
                    if st.operation == Tnames.ENDMODIFY:
                        doPop = False
                        if isinstance(block.statements[i-1].tuple[1],list):
                            if block.statements[i-1].tuple[1][0] == varName:
                                doPop = True
                        elif block.statements[i-1].tuple[1] == varName:
                            doPop = True
                            Optimizer.debugPrint("Removed modify operations",varName,"at",block.label)
                        if doPop:
                            while popCount>0:
                                block.statements.pop(popIndex)
                                popCount-=1
                            i = popIndex-1
                        break
                    i += 1
        return block

    @staticmethod
    def removeTags(block:Scope):
        i = -1
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            if st.operation in [Tnames.BEGINEXP,Tnames.ENDEXP,Tnames.BEGININIT,Tnames.ENDINIT,Tnames.BEGINMODIFY,Tnames.ENDMODIFY]:
                block.statements.pop(i)
                i -= 1
        return block

    @staticmethod
    def removeEmptyBlocks(t:TACgen):
        keys = []
        for k in t.scopes.keyOrder:
            keys.append(k)

        for i in range(0,keys.__len__()):
            if len(t.scopes.get(keys[i]).statements)==0:
                t.scopes.removeByKey(keys[i])

        for block in t.scopes.returnItemsInOrder():
            i = -1
            while True:
                i+=1
                if i >= block.statements.size():
                    break

                st = block.statements[i]
                if st.operation == Tnames.CALLBLOCK:
                    if not t.scopes.containsKey(st.tuple[1]):
                        block.statements.pop(i)
                        i-=1

    @staticmethod
    def variableIsChangedInScope(scope: Scope, variableName: str):
        for st in scope.statements:
            if st.operation in LexName.VariableModify:
                if isinstance(st.tuple[1], list):
                    if st.tuple[1][0] == variableName:
                        return True
                elif st.tuple[1] == variableName:
                    return True
        return False

    @staticmethod
    def variableIsChanged(varName, definedIn: str, startAt: Scope):
        while True:
            if startAt is None:
                return False
            if Optimizer.variableIsChangedInScope(startAt, varName):
                return True
            else:
                if definedIn == startAt.getParentLabel():
                    return Optimizer.variableIsChangedInScope(Optimizer.scopes.get(definedIn), varName)
                else:
                    startAt = Optimizer.scopes.get(startAt.getParentLabel())



    @staticmethod
    def optimizeInvariantLoopVariables(block:Scope):
        loopStartIndex,loopEndIndex = 0,0
        jump = None
        labels = []
        i = -1
        foundLoop = False
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            # can't optimize Continue or Escape blocks
            if st.operation == Tnames.LABEL:
                if ("C" not in st.tuple[1]) and ("E" not in st.tuple[1]):
                    labels.append([st.tuple[1],i])
            elif st.operation == Tnames.JUMP:
                if ("C" not in st.tuple[1]) and ("E" not in st.tuple[1]):
                    jump = [st.tuple[1],i]
        if jump is not None:
            jumpLabel = jump[0]
            for label in labels:
                if label[0] == jumpLabel:
                    if jump[1]>label[1]:
                        foundLoop = True
                        loopEndIndex = jump[1]
                        loopStartIndex = label[1]
                        break
        if foundLoop:
            Optimizer.debugPrint("FOUND LOOP",loopStartIndex,"to",loopEndIndex)
            #  optimize init to make it outside the loop
            i = loopStartIndex-1
            while True:
                i += 1
                if i >= loopEndIndex:
                    break
                st = block.statements[i]
                # initStatementIndexes = ArrayList(None,None)
                # analizingVariableName = None
                initArray = ArrayList()
                modifyArray = ArrayList()
                if st.operation == Tnames.INIT:
                    analizingVariableName = st.tuple[1][1]
                    Optimizer.debugPrint(analizingVariableName, "is maybe not modified in", block.label)
                    if not Optimizer.variableIsChanged(analizingVariableName,block.label,block):
                        Optimizer.debugPrint(analizingVariableName,"is not modified in",block.label)
                        initArray = Optimizer.extractVariable(analizingVariableName,block, False)
                        modifyArray = Optimizer.extractVariable(analizingVariableName, block, True)
                        for st in initArray:
                            Optimizer.debugPrint(st)
                        for st in modifyArray:
                            Optimizer.debugPrint(st)
                        block.statements.extendAt(modifyArray, loopStartIndex - 1)
                        block.statements.extendAt(initArray,loopStartIndex-1)

                        break


            pass
        else:
            Optimizer.debugPrint("No loop in",block.label)

        pass

    @staticmethod
    def extractVariable(varName:str,block:Scope,modify=True):
        i = -1
        if modify:
            end = Tnames.ENDMODIFY
            start = Tnames.BEGINMODIFY
        else:
            end = Tnames.ENDINIT
            start = Tnames.BEGININIT
        popped = ArrayList(None,None)
        while True:
            i += 1
            if i >= block.statements.size():
                break
            st = block.statements[i]
            popCount = 0
            if st.operation == start:
                popIndex = i
                while True:
                    popCount += 1
                    st = block.statements[i]
                    if st.operation == end:
                        doPop = False
                        if modify:
                            if isinstance(block.statements[i - 1].tuple[1], list):
                                if block.statements[i - 1].tuple[1][0] == varName:
                                    doPop = True
                            elif block.statements[i - 1].tuple[1] == varName:
                                doPop = True
                        else:
                            if block.statements[i - 1].tuple[1][1] == varName:
                                doPop = True
                        if doPop:
                            op = "init"
                            if modify:
                                op = "modify"
                            Optimizer.debugPrint("Extracted",op,"operations", varName, "at", block.label)
                            while popCount > 0:
                                popped.append(block.statements.pop(popIndex))
                                popCount -= 1
                            i = popIndex - 1
                        break
                    i += 1
        return popped



    @staticmethod
    def optimize(t:TACgen):
        Optimizer.scopes = t.scopes
        t = Optimizer.optimizeDeadCode(t)
        Optimizer.optimizeUnusedVariables(t)
        for block in t.scopes.returnItemsInOrder():
            Optimizer.optimizeInvariantLoopVariables(block)
            Optimizer.removeTags(block)
        Optimizer.removeEmptyBlocks(t)
        return t
