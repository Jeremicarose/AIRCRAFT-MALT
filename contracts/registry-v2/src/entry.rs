use ckb_std::{
    ckb_constants::Source,
    high_level::{load_cell_data, load_script, QueryIter},
    type_id::check_type_id,
};
use serde_json_core::de::from_slice;

use crate::error::Error;
use crate::record::ReceiverRegistryRecord;

fn load_record(index: usize, source: Source) -> Result<ReceiverRegistryRecord, Error> {
    let data = load_cell_data(index, source).map_err(|_| Error::Encoding)?;
    let (record, consumed) =
        from_slice::<ReceiverRegistryRecord>(&data).map_err(|_| Error::Encoding)?;
    if consumed != data.len() {
        return Err(Error::Encoding);
    }
    Ok(record)
}

pub fn main() -> Result<(), Error> {
    let script = load_script().map_err(|_| Error::InvalidIdentityArgs)?;
    if script.as_reader().args().raw_data().len() != 32 {
        return Err(Error::InvalidIdentityArgs);
    }
    check_type_id(0).map_err(|_| Error::InvalidIdentityRule)?;

    let input_count = QueryIter::new(load_cell_data, Source::GroupInput).count();
    let output_count = QueryIter::new(load_cell_data, Source::GroupOutput).count();

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
