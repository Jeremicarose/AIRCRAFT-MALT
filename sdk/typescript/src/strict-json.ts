class JsonInteger {
  constructor(readonly raw: string) {}
}

class JsonFloat {
  constructor(readonly value: number) {}
}

type StrictJsonValue =
  | null
  | boolean
  | string
  | JsonInteger
  | JsonFloat
  | StrictJsonValue[]
  | { [key: string]: StrictJsonValue };

class StrictJsonParser {
  private position = 0;

  constructor(private readonly source: string) {}

  parse(): StrictJsonValue {
    const value = this.parseValue();
    this.skipWhitespace();
    if (this.position !== this.source.length) {
      throw new Error("JSON contains trailing data");
    }
    return value;
  }

  private parseValue(): StrictJsonValue {
    this.skipWhitespace();
    const current = this.source[this.position];
    if (current === "{") return this.parseObject();
    if (current === "[") return this.parseArray();
    if (current === '"') return this.parseString();
    if (current === "t") return this.parseLiteral("true", true);
    if (current === "f") return this.parseLiteral("false", false);
    if (current === "n") return this.parseLiteral("null", null);
    return this.parseNumber();
  }

  private parseObject(): { [key: string]: StrictJsonValue } {
    this.position += 1;
    const result: { [key: string]: StrictJsonValue } = {};
    const keys = new Set<string>();
    this.skipWhitespace();
    if (this.source[this.position] === "}") {
      this.position += 1;
      return result;
    }

    while (true) {
      this.skipWhitespace();
      if (this.source[this.position] !== '"') {
        throw new Error("JSON object keys must be strings");
      }
      const key = this.parseString();
      if (keys.has(key)) {
        throw new Error(`JSON contains duplicate field: ${key}`);
      }
      keys.add(key);
      this.skipWhitespace();
      if (this.source[this.position] !== ":") {
        throw new Error("JSON object key is missing a colon");
      }
      this.position += 1;
      result[key] = this.parseValue();
      this.skipWhitespace();
      const separator = this.source[this.position];
      if (separator === "}") {
        this.position += 1;
        return result;
      }
      if (separator !== ",") {
        throw new Error("JSON object is missing a comma");
      }
      this.position += 1;
    }
  }

  private parseArray(): StrictJsonValue[] {
    this.position += 1;
    const result: StrictJsonValue[] = [];
    this.skipWhitespace();
    if (this.source[this.position] === "]") {
      this.position += 1;
      return result;
    }

    while (true) {
      result.push(this.parseValue());
      this.skipWhitespace();
      const separator = this.source[this.position];
      if (separator === "]") {
        this.position += 1;
        return result;
      }
      if (separator !== ",") {
        throw new Error("JSON array is missing a comma");
      }
      this.position += 1;
    }
  }

  private parseString(): string {
    const start = this.position;
    this.position += 1;
    while (this.position < this.source.length) {
      const character = this.source[this.position];
      if (character === '"') {
        this.position += 1;
        return JSON.parse(this.source.slice(start, this.position)) as string;
      }
      if (character === "\\") {
        throw new Error("JSON string escape sequences are not permitted");
      }
      if (character !== undefined && character.charCodeAt(0) < 0x20) {
        throw new Error("JSON string contains an unescaped control character");
      }
      this.position += 1;
    }
    throw new Error("JSON string is not terminated");
  }

  private parseNumber(): JsonFloat | JsonInteger {
    const remaining = this.source.slice(this.position);
    const match = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(remaining);
    if (!match) throw new Error("JSON contains an invalid value");
    const raw = match[0];
    this.position += raw.length;
    if (!raw.includes(".") && !/[eE]/.test(raw)) return new JsonInteger(raw);
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error("JSON number is outside the f64 range");
    return new JsonFloat(value);
  }

  private parseLiteral<T extends null | boolean>(literal: string, value: T): T {
    if (this.source.slice(this.position, this.position + literal.length) !== literal) {
      throw new Error("JSON contains an invalid literal");
    }
    this.position += literal.length;
    return value;
  }

  private skipWhitespace(): void {
    while ([" ", "\t", "\n", "\r"].includes(this.source[this.position] ?? "")) {
      this.position += 1;
    }
  }
}

export function parseStrictJson(source: string): StrictJsonValue {
  return new StrictJsonParser(source).parse();
}

export function isJsonInteger(value: unknown): value is JsonInteger {
  return value instanceof JsonInteger;
}

export function isJsonFloat(value: unknown): value is JsonFloat {
  return value instanceof JsonFloat;
}
