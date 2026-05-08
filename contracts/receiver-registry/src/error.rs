#[derive(Debug, PartialEq)]
pub enum Error {
    Encoding,
    MissingReceiverId,
    InvalidLatitude,
    InvalidLongitude,
    InvalidAltitude,
    InvalidStatus,
    MissingCapabilities,
    MissingModeS,
    InvalidTimestamp,
    InvalidStreamProtocol,
    InvalidStreamFormat,
}

impl Error {
    pub fn as_i8(&self) -> i8 {
        match self {
            Error::Encoding => -2,
            Error::MissingReceiverId => -10,
            Error::InvalidLatitude => -11,
            Error::InvalidLongitude => -12,
            Error::InvalidAltitude => -13,
            Error::InvalidStatus => -14,
            Error::MissingCapabilities => -15,
            Error::MissingModeS => -16,
            Error::InvalidTimestamp => -17,
            Error::InvalidStreamProtocol => -18,
            Error::InvalidStreamFormat => -19,
        }
    }
}
