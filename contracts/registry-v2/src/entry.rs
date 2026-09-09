use crate::error::Error;
use crate::record::{decode_registry_v2_record, ReceiverRegistryRecord, MAX_RECORD_BYTES};
use ckb_std::{
    ckb_constants::Source,
    high_level::{load_cell_capacity, load_script, QueryIter},
    syscalls,
    type_id::check_type_id,
};

fn load_record(index: usize, source: Source) -> Result<ReceiverRegistryRecord, Error> {
    let mut data = [0u8; MAX_RECORD_BYTES];
    let length =
        syscalls::load_cell_data(&mut data, 0, index, source).map_err(|_| Error::Encoding)?;
    decode_registry_v2_record(&data[..length])
}

pub fn main() -> Result<(), Error> {
    let script = load_script().map_err(|_| Error::InvalidIdentityArgs)?;
    if script.as_reader().args().raw_data().len() != 32 {
        return Err(Error::InvalidIdentityArgs);
    }
    check_type_id(0).map_err(|_| Error::InvalidIdentityRule)?;

    let input_count = QueryIter::new(load_cell_capacity, Source::GroupInput).count();
    let output_count = QueryIter::new(load_cell_capacity, Source::GroupOutput).count();

    match (input_count, output_count) {
        (0, 1) => load_record(0, Source::GroupOutput)?.validate_creation(),
        (1, 1) => {
            let previous = load_record(0, Source::GroupInput)?;
            let next = load_record(0, Source::GroupOutput)?;
            next.validate_successor(&previous)
        }
        _ => Err(Error::InvalidCardinality),
    }
}
