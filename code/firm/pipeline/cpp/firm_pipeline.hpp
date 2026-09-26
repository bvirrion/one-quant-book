// firm.pipeline -- hot-path stages composed at compile time (build of One Quant Book 13, chapter 7). C++20.
// A stage is any type with `bool on(E&)` (false stops the event); Pipeline<E, S...> calls them in order through a fold
// expression, so the compiler sees every call and can inline the whole path. DynPipeline<E> does the same through
// virtual calls, for tests and for configurations chosen at run time.
#pragma once
#include <concepts>
#include <memory>
#include <tuple>
#include <utility>
#include <vector>

namespace firm::pipeline {

template <class S, class E>
concept Stage = requires(S s, E& e) {
    { s.on(e) } -> std::same_as<bool>;
};

template <class E, Stage<E>... S>
class Pipeline {
public:
    Pipeline() = default;
    explicit Pipeline(S... s) : stages_(std::move(s)...) {}
    // Stops at the first stage that returns false; && is short-circuit inside the fold.
    bool on(E& e) {
        return std::apply([&](auto&... s) { return (s.on(e) && ...); }, stages_);
    }
    template <std::size_t I>
    auto& stage() { return std::get<I>(stages_); }

private:
    std::tuple<S...> stages_;
};

// The runtime-polymorphic version: one indirect call per stage per event.
template <class E>
struct AnyStage {
    virtual ~AnyStage() = default;
    virtual bool on(E& e) = 0;
};

template <class E, class S>
struct StageAdapter final : AnyStage<E> {
    S s;
    explicit StageAdapter(S x) : s(std::move(x)) {}
    bool on(E& e) override { return s.on(e); }
};

template <class E>
class DynPipeline {
public:
    template <class S>
    void add(S s) { stages_.push_back(std::make_unique<StageAdapter<E, S>>(std::move(s))); }
    bool on(E& e) {
        for (auto& s : stages_)
            if (!s->on(e)) return false;
        return true;
    }

private:
    std::vector<std::unique_ptr<AnyStage<E>>> stages_;
};

}  // namespace firm::pipeline
