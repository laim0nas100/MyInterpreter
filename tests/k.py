from src.lib import OrderedMap, ArrayList

m = OrderedMap()
m.put("1",1)
m.put("2",2)
m.put("4",4)
m.put("3",3)

print(m.returnItemsInOrder())


a = ArrayList()
a.append(2)
a.append(3)
a.extendAt([0,1],0)
print(a)