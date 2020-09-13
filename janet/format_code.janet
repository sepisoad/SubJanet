(import spork/fmt)

(def text ((dyn :args) 1))
(def res (fmt/format text))
(prin res)