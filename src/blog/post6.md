I have recently been using [Googletest](https://github.com/google/googletest) quite a bit for various projects I'm working on. For the most part, I've had a great experience with this: after a little bit of [setup hassle](https://github.com/google/googletest/blob/master/googletest/README.md#incorporating-into-an-existing-cmake-project), you get a very extensible unit test framework completely integrated with CMake!

## A Basic Problem
Last week, however, I ran into a problem, which I will briefly set up here:

I have a function that is templated by non-type parameters. For example,

```cpp
template<bool parallel>
int sort(std::vector<int> &a) {
  // sorts in parallel if [parallel], else in serial.
}
```
<span class="caption">A templated sort function that I'd like to test.</span>

I want to write the same set of unit tests for the serial and parallel versions of this function, something like the following:

```cpp
template<bool parallel>
class SortTest : public testing::Test {};

TEST*(SortTest, Test1) {
  // test sort<parallel>(...)
}
```
<span class="caption">Ideally, I'd be able to test it like this.</span>

However, when I looked through the [advanced guide](https://github.com/google/googletest/blob/master/docs/advanced.md) for Googletest, I saw that they only offer two generalizable testing options: 

- [Value-Parameterized](https://github.com/google/googletest/blob/master/docs/advanced.md#value-parameterized-tests)
- [Typed](https://github.com/google/googletest/blob/master/docs/advanced.md#typed-tests) (I like to refer to these as type-templated, for parallel structure). 

Unfortunately, this doesn't quite cut it. Specifically, the value parameters of value-parameterized tests (accessed through `GetParam()` within tests) are not compile-time constants, so I can't use them to template my function as I described above. Now, my first solution for this conundrum was to do the following with value-parameterized tests:

```cpp
class SortTest : public testing::TestWithParam<bool> {};

TEST_P(SortTest, Test1) {
  if(GetParam()) {
    // test sort<true>(...)
  } else {
    // test sort<false>(...)
  }
}
```
<span class="caption">A hacky solution to convert runtime constants to compile-time constants...not very satisfying.</span>

This works, but it doesn't feel very satisfying (definitely not blog-post worthy!). More concretely though, this is not as extensible as I would like. 

## A More Involved Problem
In particular, consider this new setup (which is closer to what I was working with):

```cpp
template<bool parallel>
class BST {
  // interface for a BST, with basic shared functionality
};

template<bool parallel>
class AVL : public BST<parallel> {
  // implement the BST interface with AVL heuristics
};

template<bool parallel>
class RBT : public BST<parallel> {
  // implement the BST interface with RBT heuristics
};
```
<span class="caption">A new minimal example of classes I'd like to test.</span>

Then, I would like to write shared tests for all trees that implement the `BST` interface. However, I would like to do some tests that are specific to each type (i.e. verify that the nodes are laid out in the correct order in memory, for example). Even with these specific tests, though, I want to have some underlying shared structure (i.e. it will construct and return a tree of a given - templated - type which I can then run specific tests on). The basic structure of what I would like (but is again impossible on Googletest) is shown below:

```cpp
template<class Tree>
class BSTTestResources : public ::testing::Test {
  public:
  // provide several shared resources for constructing BST tests

  // for example:
  static Tree CONSTRUCT_SIZE_100() { /*...*/ }
};

template<bool parallel>
class TestAVLStructure : public BSTTestResources<AVL<parallel>> {};

template<bool parallel>
class TestRBTStructure : public BSTTestResources<RBT<parallel>> {};
```
<span class="caption">Ideally, I would have this test structure. The hack from before no longer works.</span>

As noted before, however, this is impossible: we can't template test classes with values. Furthermore, our previous hack of branching on the value of the parameter no longer works either: we can't use `GetParam()` to access the parameter in the template list for the base class `BSTTestResources`. Granted, this seems to be a somewhat contrived example, but it came up in my real usage, and I imagine others have run into it at some point.

You could get around this in theory by letting `TestAVLStructure` and `TestRBTStructure` both be Typed test classes, and just passing the entire `AVL<parallel>` or `RBT<parallel>` (respectively) class in to generate the tests. This works, and I do use it for some of my tests. However, it doesn't express the same level of specificity that the structure I've written above does - the tests above impose, for example, the restriction that `TestAVLStructure` is only for the class `AVL<>`, and I'd like to maintain this semantic structure.

## A Solution
Luckily, there is a way to get around the entire issue. Specifically, we can (also hackily) encode values into types, and use type-parameterized tests to pass compile-time values. In code,

```cpp
class True {
  static constexpr bool v = true;
};

class False {
  static constexpr bool v = false;
};
```
<span class="caption">Encode parameter values into types!</span>

Now, I can write the above tree tests as:

```cpp
template<class Tree>
class BSTTestResources : public ::testing::Test {
  public:
  // provide several shared resources for constructing BST tests

  // for example:
  static Tree CONSTRUCT_SIZE_100() { /*...*/ }
};

template<typename Parallel>
class TestAVLStructure : public BSTTestResources<AVL<Parallel::v>> {};

template<typename Parallel>
class TestRBTStructure : public BSTTestResources<RBT<Parallel::v>> {};
```
<span class="caption">Finally! "Value"-templated tests. </span>

This accomplishes all my goals: I get to share an underlying test class with shared resources and I get to maintain the semantic structure of my specialized tests, which should only be applicable to the tree type that they are written for. The trick here is that types in C++ can be arbitrarily augmented with values by using `static constexpr`. I really liked this idea more broadly, because it gives types some notion of value, so it lets us start thinking about types as ever-so-slightly closer to first-class citizens they normally are in C++.
