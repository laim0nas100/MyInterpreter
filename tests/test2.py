import inspect
class A:
    className = "A"
    @classmethod
    def f(self):
        return self.className


class B(A):
    className = "B"
    @classmethod
    def f(self):
        return self.className + super().f()


class C(B):
    className = "C"
    @classmethod
    def f(self):
        return self.className + super().f()

b = B()
print(b.f())
c= C()
print(c.f())
print("čęęčė")