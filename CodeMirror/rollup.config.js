import {nodeResolve} from "@rollup/plugin-node-resolve"
import typescript from "@rollup/plugin-typescript"
export default {
  input: "./editor.js",
  output: {
    file: "./editor.bundle.js",
    format: "umd",
    name: "editor"
  },
  plugins: [
    nodeResolve(),
    typescript({compilerOptions: {
      lib: ["es5", "es6", "dom"],
      target: "es6"
    }})
  ]
}