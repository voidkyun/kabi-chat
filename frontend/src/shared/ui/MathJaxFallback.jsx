import { MathJax, MathJaxContext } from "better-react-mathjax";

const MATHJAX_CONFIG = {
  loader: {
    load: ["input/tex", "output/chtml"],
  },
  tex: {
    displayMath: [
      ["$$", "$$"],
      ["\\[", "\\]"],
    ],
    inlineMath: [
      ["$", "$"],
      ["\\(", "\\)"],
    ],
  },
};

export default function MathJaxFallback({ displayMode, expression }) {
  return (
    <MathJaxContext config={MATHJAX_CONFIG}>
      <MathJax dynamic inline={!displayMode} hideUntilTypeset="first">
        {expression}
      </MathJax>
    </MathJaxContext>
  );
}
