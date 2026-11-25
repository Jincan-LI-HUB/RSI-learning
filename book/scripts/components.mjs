import vm from "node:vm";
import readline from "node:readline";

const tags = new Set(("AsyncImage Chart box card caption grid grid-item row title text icon math spacer divider label line slider rect circle path svg g ellipse table table-cell table-row list list-item badge checkbox radio radio-group input button segmented-control Link Cite MemoryCite Entity").split(" "));
const tagStart = /^<\/?([A-Za-z][\w-]*)(?=[\s/>])/;
const dangerous = /\b(?:constructor|prototype|__proto__|require|process|globalThis|eval|Function|Proxy|Reflect|WebAssembly|import|fetch|Worker|setTimeout|setInterval)\b|\\u(?:\{|[0-9a-f]{4})/i;
const ignored = /^(on[A-Z]|disabled$)/;

function balanced(source, start) {
  const close = { "{": "}", "[": "]", "(": ")" };
  const stack = [close[source[start]]];
  let quote = "";
  for (let i = start + 1; i < source.length; i++) {
    const ch = source[i];
    if (quote) {
      if (ch === "\\") ++i;
      else if (ch === quote) quote = "";
    } else if ("\"'".includes(ch) || ch.charCodeAt(0) === 96) quote = ch;
    else if (ch in close) stack.push(close[ch]);
    else if (ch === stack.at(-1)) {
      stack.pop();
      if (!stack.length) return i + 1;
    }
  }
  throw Error("unbalanced bracket");
}

function expression(code) {
  const operators = code.replace(/"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'/g,
    (literal) => dangerous.test(literal.slice(1,-1).trim()) && !/\s/.test(literal.slice(1,-1)) ? literal : '""');
  if (dangerous.test(operators) || /(?:^|[^\w])new\s/.test(operators)) throw Error("Disallowed expression");
  // The archived volatility template used mathematical unary-minus notation
  // before exponentiation. JavaScript requires its evaluation order explicit.
  return code.replaceAll("Math.exp(-((u-.32)/.1)**2)", "Math.exp(-(((u-.32)/.1)**2))")
             .replaceAll("Math.exp(-((u-.78)/.11)**2)", "Math.exp(-(((u-.78)/.11)**2))");
}

function compile(source) {
  let code = "", cursor = 0, buffer = "";
  function add(s) { code += "out.push(" + s + ");\n"; }
  function flush() {
    if (buffer) { add("['t'," + JSON.stringify(buffer) + "]"); buffer = ""; }
  }
  while (cursor < source.length) {
    const start = source[cursor];
    if (start === "{" && !source.startsWith("{}", cursor)) {
      const tail = balanced(source, cursor);
      const value = source.slice(cursor+1, tail-1).trim();
      flush();
      if (value.startsWith("@body ")) {
        const declaration = expression(value.slice(6)).replace(/;$/, "");
        if (!/^const\s/.test(declaration)) throw Error("Expected a const declaration");
        code += declaration + ";\n";
      } else if (value.startsWith("#each ")) {
        const group = value.slice(6).match(/^([\s\S]+)\s+as\s+([$_\w]+)(?:\s*,\s*([$_\w]+))?$/);
        if (!group) throw Error("Unsupported loop");
        code += "Array.from(" + expression(group[1]) + ").forEach((" + group[2] + (group[3] ? "," + group[3] : "") + ")=>{\n";
      } else if (value === "/each") code += "});\n";
      else if (value.startsWith("#if ")) code += "if(" + expression(value.slice(4)) + "){\n";
      else if (value === ":else") code += "}else{\n";
      else if (value.startsWith(":else if ")) code += "}else if(" + expression(value.slice(9)) + "){\n";
      else if (value === "/if") code += "}\n";
      else add("['t',String(" + expression(value) + ")]");
      cursor = tail;
      continue;
    }
    const match = start === "<" && source.slice(cursor).match(tagStart);
    if (!match || !tags.has(match[1])) { buffer += start; ++cursor; continue; }
    flush();
    const name = match[1];
    if (source[cursor+1] === "/") {
      add(JSON.stringify(["c",name]));
      cursor = source.indexOf(">", cursor)+1;
      continue;
    }
    cursor += match[0].length;
    const props = [];
    for (;;) {
      const rest = source.slice(cursor);
      const end = rest.match(/^\s*(\/?>)/);
      if (end) {
        add("['o'," + JSON.stringify(name) + ",{" + props.join(",") + "}," + String(end[1]==="/>") + "]");
        cursor += end[0].length;
        break;
      }
      const key = rest.match(/^\s*([\w:-]+)\s*(=?)/);
      if (!key) throw Error("Unsupported attribute: " + rest.slice(0,60));
      cursor += key[0].length;
      let prop = "true";
      if (key[2]) {
        while (/\s/.test(source[cursor])) ++cursor;
        if (source[cursor] === "{") {
          const tail = balanced(source, cursor);
          const body = source.slice(cursor+1,tail-1);
          if (!ignored.test(key[1])) prop = "(" + expression(body) + ")";
          cursor = tail;
        } else {
          const quote = source[cursor++];
          if (!"\"'".includes(quote)) throw Error("Expected a quoted attribute");
          const begin = cursor;
          for (;cursor < source.length;cursor++) {
            if (source[cursor] === "\\") ++cursor;
            else if (source[cursor] === quote) break;
          }
          prop = JSON.stringify(source.slice(begin,cursor++));
        }
      }
      if (!ignored.test(key[1])) props.push(JSON.stringify(key[1])+":"+prop);
    }
  }
  flush();
  return code;
}

const input = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
for await (const line of input) {
  let generated = "";
  try {
    const {source, overrides, refs} = JSON.parse(line);
    generated = compile(source);
    const state = JSON.stringify(overrides || {});
    const sources = JSON.stringify(refs || {});
    const script = "'use strict';\nconst out=[]; const states=[]; const override="+state+";\n"
      + "const DIL={useState(defaultValue){const i=states.length; states.push(defaultValue); return [Object.hasOwn(override,i)?override[i]:defaultValue,()=>{}];}};\n"
      + "const refs="+sources+";\n"
      + "for(const [key,value] of Object.entries(refs)) globalThis[key]={url:{uri:value}};\n"
      + generated + "\nJSON.stringify({events:out,states});";
    console.log(vm.runInNewContext(script, Object.create(null),
      {timeout:1200, contextCodeGeneration:{strings:false, wasm:false}}));
  } catch (error) {
    console.log(JSON.stringify({error:String(error.message), generated:generated.slice(-280)}));
  }
}
