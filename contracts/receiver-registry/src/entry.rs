use ckb_std::{
    ckb_constants::Source,
    high_level::load_cell_data,
};
use serde_json_core::de::from_slice;

use crate::error::Error;
use crate::record::ReceiverRegistryRecord;


pub fn main() -> Result<(), Error> {
    let data = load_cell_data(0, Source::GroupInput).map_err(|_| Error::Encoding)?;
    let (record, _consumed) =
        from_slice::<ReceiverRegistryRecord>(&data).map_err(|_| Error::Encoding)?;
    record.validate()
}
