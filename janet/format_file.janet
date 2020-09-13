(import spork/fmt)

(def file (get (dyn :args) 1))
(fmt/format-file file)
