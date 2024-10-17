pub mod built_info {
    include!(concat!(env!("OUT_DIR"), "/built.rs"));
}

pub mod sources;
pub mod template;

use clap::{Parser, Subcommand};
use dialoguer::Confirm;
use is_url::is_url;
use std::{fs, path::PathBuf};

#[derive(Parser)]
#[command(version)]
#[command(about = "Simplified source code generator", long_about = None)]
struct Cli {
	#[command(subcommand)]
	command: Option<Commands>,
	#[arg(short, long, help = "Toggle verbose information")]
	verbose: bool,
}

#[derive(Subcommand)]
enum Commands {
	#[command(about = "Generate source code using a template")]
	Generate {
		#[arg(help = "Template to use for generating source code")]
		template: String,
		#[arg(short, long, help = "Specify output directory")]
		output: Option<String>
	},
	#[command(about = "Sync other sources to latest changes")]
	Sync {},
	#[command(about = "List all templates from sources")]
	List {
		#[arg(short, long, help = "Only include templates from local source")]
		local: bool
	},
	#[command(about = "Import local template from file")]
	Import {
		#[arg(help = "The file to be imported as a template")]
		file: PathBuf
	},
	#[command(about = "Export template from local source to file")]
	Export {
		#[arg(help = "The name of the selected template to be exported")]
		template: String,
		#[arg(help = "The output directory where the template will be exported")]
		output: PathBuf
	},
	#[command(about = "Remove existing template from local source")]
	Remove {
		#[arg(help = "The name of the selected template to be removed")]
		template: String
	},
	#[command(about = "Add a new source")]
	SourceAdd {
		#[arg(help = "The name of the new source")]
		source: String,
		#[arg(help = "The URL of the new source")]
		url: String
	},
	#[command(about = "Edit an existing source")]
	SourceEdit {
		#[arg(help = "The name of the existing source to be edited")]
		source: String,
		#[arg(help = "The new URL of the existing source")]
		new_url: String
	},
	#[command(about = "Remove an existing source")]
	SourceRemove {
		#[arg(help = "The name of the existing source to be removed")]
		source: String
	},
	#[command(about = "Remove all sources & delete everything")]
	Reset {
		#[arg(short, long, help = "Forcefully perform operation")]
		force: bool
	}
}

fn main() {
	// Parse command-line arguments using the clap library
	// Also initialize the sources INI file (or if does not exist, create a new one)
	let cli = Cli::parse();

	// Once parsed, we can use match statements to call different functions
	// (e.g if "generate" is the subcommand, then we go to the generate block)
	match &cli.command {
		Some(Commands::SourceAdd { source, url }) => 'source_add: {
			if !is_url(url) {
				eprintln!("Failed to add new source: \"{}\" (URL malformed or invalid)", source);
				break 'source_add;
			}

			let mut sources = sources::init().unwrap_or(sources::new());
			if sources.general_section().contains_key(source) {
				eprintln!("Failed to add new source: \"{}\" (Already exists)", source);
				break 'source_add;
			}
			
			let mut sources_section = sources.with_general_section();
			sources_section.add(source, url);
			let result = sources::write(sources);

			if let Err(..) = result {
				eprintln!("An error occurred while trying to add a source");
			} else {
				println!("Added new source: \"{}\" = \"{}\"", source, url);
			}
		}
		Some(Commands::SourceEdit { source, new_url }) => 'source_edit: {
			if !is_url(new_url) {
				eprintln!("Failed to edit existing source: \"{}\" (New URL malformed or invalid)", source);
				break 'source_edit;
			}

			let mut sources = sources::init().unwrap_or(sources::new());
			if !sources.general_section().contains_key(source) {
				eprintln!("Failed to edit existing source: \"{}\" (Does not exist)", source);
				break 'source_edit;
			}

			let mut sources_section = sources.with_general_section();
			sources_section.set(source, new_url);
			let result = sources::write(sources);

			if let Err(..) = result {
				eprintln!("An error occurred while trying to add a source");
			} else {
				println!("Changed existing source: \"{}\" = \"{}\"", source, new_url);
			}
		}
		Some(Commands::Reset { force }) => 'reset: {
			// If force isn't set or is set to false, we must confirm the user
			// if they really want to wipe everything or not
			if !force {
				let confirmed = Confirm::new()
										.with_prompt("Perform a reset operation?")
										.interact()
										.unwrap();
				if !confirmed {
					// abort operation if user said no
					break 'reset;
				}
			}

			// Locate application data directory
			let dirs = vec![sources::dir_path()];
			for directory in dirs {
				if !directory.is_dir() {
					println!("Skipped: \"{}\" (already wiped)", directory.display());
					continue;
				}

				let result = fs::remove_dir_all(directory.clone());
				if let Err(..) = result { 
					eprintln!("Wipe failed: \"{}\" ({})", directory.display(), result.unwrap_err());
				} else {
					println!("Wiped: \"{}\"", directory.display());
				}
			}
		}
		_ => {}
	}

	// TODO: Implement more stuff, if anyone can ;)
}
