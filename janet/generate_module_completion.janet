(defn no-side-effects  
  [src]
  (cond
    (tuple? src)
    (if (= (tuple/type src) :brackets)
      (all no-side-effects src))
    (array? src)
    (all no-side-effects src)
    (dictionary? src)
    (and (all no-side-effects (keys src))
         (all no-side-effects (values src)))
    true))

(defn is-safe-def [x] (no-side-effects (last x)))

(def safe-forms {'defn true 'defn- true 'defmacro true 'defmacro- true
                  'def is-safe-def 'var is-safe-def 'def- is-safe-def 'var- is-safe-def
                  'defglobal is-safe-def 'varglobal is-safe-def})

(def importers {'import true 'import* true 'dofile true 'require true})

(defn use-2 [evaluator args]
  (each a args (import* (string a) :prefix "" :evaluator evaluator)))

(defn evaluator
    [thunk source env where]
    (if true #*compile-only*
      (when (tuple? source)
        (def head (source 0))
        (def safe-check (safe-forms head))
        (cond
          # Sometimes safe form
          (function? safe-check)
          (if (safe-check source) (thunk))
          # Always safe form
          safe-check
          (thunk)
          # Use
          (= 'use head)
          (use-2 evaluator (tuple/slice source 1))
          # Import-like form
          (importers head)
          (do
            (let [[l c] (tuple/sourcemap source)
                  newtup (tuple/setmap (tuple ;source :evaluator evaluator) l c)]
              ((compile newtup env where))))))
      (thunk)))

(defn mod-filter
  [x path]
  (case (type x)
    :nil path
    :string (string/has-suffix? x path)
    (x path)))

(def file ((dyn :args) 1))

(var env (dofile file :env (make-env) :evaluator evaluator (comment :expander expander) ))
(map |(prin $ " ") (sort (keys env)))