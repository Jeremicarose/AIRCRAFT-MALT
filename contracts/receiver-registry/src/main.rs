#![no_std]
#![cfg_attr(not(test), no_main)]

extern crate alloc;

mod entry;
mod error;
mod record;

#[cfg(not(test))]
ckb_std::entry!(program_entry);

#[cfg(not(test))]
fn program_entry() -> i8 {
    match entry::main() {
        Ok(()) => 0,
        Err(error) => error.as_i8(),
    }
}
