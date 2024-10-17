use crate::built_info;
use directories::ProjectDirs;
use ini::{Error, Ini};
use std::{fs , io::Result as IoResult, path::PathBuf};

pub fn init() -> Result<Ini, Error> {
    return Ini::load_from_file(path());
}

pub fn new() -> Ini {
    let mut ini = Ini::new();
    ini.with_section(None::<String>).add("local", "LOCAL");
    return ini;
}

pub fn write(ini: Ini) -> IoResult<()> {
    let path = path();
    fs::create_dir_all(path.parent().unwrap())?;
    return ini.write_to_file(path);
}

pub fn path() -> PathBuf {
    return dir_path().join("sources.ini");
}

pub fn dir_path() -> PathBuf {
    let project_dirs = ProjectDirs::from("", "", built_info::PKG_NAME);
    return project_dirs.as_ref().unwrap().config_local_dir().to_path_buf();
}
