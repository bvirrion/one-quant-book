//! A minimal JSON reader for the simulator's configuration (objects, arrays, strings, integers, booleans, null).

use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Default)]
pub enum Value {
    #[default]
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Arr(Vec<Value>),
    Obj(BTreeMap<String, Value>),
}

impl Value {
    pub fn get(&self, k: &str) -> Option<&Value> {
        match self {
            Value::Obj(m) => m.get(k),
            _ => None,
        }
    }
    pub fn int(&self, k: &str, dflt: i64) -> i64 {
        match self.get(k) {
            Some(Value::Int(i)) => *i,
            _ => dflt,
        }
    }
    pub fn str(&self, k: &str, dflt: &str) -> String {
        match self.get(k) {
            Some(Value::Str(s)) => s.clone(),
            _ => dflt.to_string(),
        }
    }
    pub fn arr(&self, k: &str) -> &[Value] {
        match self.get(k) {
            Some(Value::Arr(a)) => a,
            _ => &[],
        }
    }
}

pub fn parse(text: &str) -> Result<Value, String> {
    let b = text.as_bytes();
    let mut p = 0usize;
    let v = value(b, &mut p)?;
    ws(b, &mut p);
    if p != b.len() {
        return Err("trailing characters".into());
    }
    Ok(v)
}

fn ws(b: &[u8], p: &mut usize) {
    while *p < b.len() && b[*p].is_ascii_whitespace() {
        *p += 1;
    }
}

fn string(b: &[u8], p: &mut usize) -> Result<String, String> {
    ws(b, p);
    if b.get(*p) != Some(&b'"') {
        return Err("expected string".into());
    }
    *p += 1;
    let mut out = Vec::new();
    while *p < b.len() && b[*p] != b'"' {
        if b[*p] == b'\\' {
            *p += 1;
        }
        out.push(b[*p]);
        *p += 1;
    }
    *p += 1;
    String::from_utf8(out).map_err(|e| e.to_string())
}

fn value(b: &[u8], p: &mut usize) -> Result<Value, String> {
    ws(b, p);
    match b.get(*p) {
        Some(b'{') => {
            *p += 1;
            let mut m = BTreeMap::new();
            ws(b, p);
            if b.get(*p) == Some(&b'}') {
                *p += 1;
                return Ok(Value::Obj(m));
            }
            loop {
                let k = string(b, p)?;
                ws(b, p);
                if b.get(*p) != Some(&b':') {
                    return Err("expected ':'".into());
                }
                *p += 1;
                m.insert(k, value(b, p)?);
                ws(b, p);
                match b.get(*p) {
                    Some(b',') => *p += 1,
                    Some(b'}') => {
                        *p += 1;
                        return Ok(Value::Obj(m));
                    }
                    _ => return Err("expected ',' or '}'".into()),
                }
            }
        }
        Some(b'[') => {
            *p += 1;
            let mut a = Vec::new();
            ws(b, p);
            if b.get(*p) == Some(&b']') {
                *p += 1;
                return Ok(Value::Arr(a));
            }
            loop {
                a.push(value(b, p)?);
                ws(b, p);
                match b.get(*p) {
                    Some(b',') => *p += 1,
                    Some(b']') => {
                        *p += 1;
                        return Ok(Value::Arr(a));
                    }
                    _ => return Err("expected ',' or ']'".into()),
                }
            }
        }
        Some(b'"') => Ok(Value::Str(string(b, p)?)),
        Some(b't') => {
            *p += 4;
            Ok(Value::Bool(true))
        }
        Some(b'f') => {
            *p += 5;
            Ok(Value::Bool(false))
        }
        Some(b'n') => {
            *p += 4;
            Ok(Value::Null)
        }
        _ => {
            let start = *p;
            if b.get(*p) == Some(&b'-') {
                *p += 1;
            }
            while *p < b.len() && b[*p].is_ascii_digit() {
                *p += 1;
            }
            std::str::from_utf8(&b[start..*p])
                .map_err(|e| e.to_string())?
                .parse::<i64>()
                .map(Value::Int)
                .map_err(|e| e.to_string())
        }
    }
}
