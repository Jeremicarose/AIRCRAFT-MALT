#![no_std]
#![cfg_attr(not(test), no_main)]

mod entry;
mod error;
mod record;

const ALLOC_HEAP_BYTES: usize = 4 * 1024;
const ALLOC_FALLBACK_BYTES: usize = 64 * 1024;

#[cfg(not(test))]
ckb_std::default_alloc!(ALLOC_HEAP_BYTES, ALLOC_FALLBACK_BYTES, 64);

#[cfg(not(test))]
ckb_std::entry!(program_entry);

#[cfg(not(test))]
fn program_entry() -> i8 {
    match entry::main() {
        Ok(()) => 0,
        Err(error) => error.as_i8(),
    }
}
