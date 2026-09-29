// The pybind11 binding of firm::natext (One Quant Book 15, chapter 9). Inputs are numpy arrays taken by the buffer
// protocol without copying: c_style without forcecast, so a strided or wrongly typed array is refused, not copied.
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <stdexcept>

#include "firm_natext.hpp"

namespace py = pybind11;
using Doubles = py::array_t<double, py::array::c_style>;
using Ints = py::array_t<std::int64_t, py::array::c_style>;

static Doubles ewma(const Doubles& x, double alpha) {
    const auto n = static_cast<std::size_t>(x.size());
    Doubles out(static_cast<py::ssize_t>(n));
    const double* in = x.data();
    double* o = out.mutable_data();
    {
        py::gil_scoped_release unlocked;  // pure C++ from here: other Python threads may run
        firm::natext::ewma(in, n, alpha, o);
    }
    return out;
}

static void ewma_into(const Doubles& x, double alpha, Doubles& out) {
    if (out.size() != x.size()) throw std::invalid_argument("out must have the length of x");
    const double* in = x.data();
    double* o = out.mutable_data();  // writes into the caller's array: zero copies either way
    py::gil_scoped_release unlocked;
    firm::natext::ewma(in, static_cast<std::size_t>(x.size()), alpha, o);
}

static Ints asof_index(const Ints& left, const Ints& right) {
    Ints out(left.size());
    const std::int64_t* l = left.data();
    const std::int64_t* r = right.data();
    std::int64_t* o = out.mutable_data();
    py::gil_scoped_release unlocked;
    firm::natext::asof_index(l, static_cast<std::size_t>(left.size()), r, static_cast<std::size_t>(right.size()), o);
    return out;
}

PYBIND11_MODULE(natext_cpp, m) {
    m.doc() = "firm.natext kernels in C++20 (pybind11)";
    m.def("ewma", &ewma, py::arg("x").noconvert(), py::arg("alpha"));
    m.def("ewma_into", &ewma_into, py::arg("x").noconvert(), py::arg("alpha"), py::arg("out").noconvert());
    m.def("asof_index", &asof_index, py::arg("left").noconvert(), py::arg("right").noconvert());
    m.def("ewma_step", &firm::natext::ewma_step);
}
