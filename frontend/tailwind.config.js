export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18201c",
        field: "#f6f7f3",
        line: "#d9ded8",
        guard: {
          50: "#ecf7f1",
          100: "#d5ebdf",
          600: "#24735c",
          700: "#185542",
        },
        signal: {
          red: "#a83d36",
          amber: "#9b682b",
        },
      },
      boxShadow: {
        panel: "0 14px 40px rgba(28, 38, 33, 0.08)",
      },
    },
  },
  plugins: [],
};
