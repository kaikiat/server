use std::fs::{File};
use std::io::prelude::*;

#[macro_use] extern crate rocket;

#[get("/healthz")]
fn index() -> &'static str {
    "Ok"
}

#[get("/update-k?<k>")]
fn update_k(k: String) -> &'static str {
    let filename = "k.txt";
    if let Err(e) = std::fs::remove_file(filename) {
        if e.kind() != std::io::ErrorKind::NotFound {
            return "Not Ok"
        }
    } else {
        println!("File removed");
    }

    let mut file = File::create(filename).expect("Error creating ");
    file.write_all(k.as_bytes()).expect("Error writing to file");
    "Ok"
}

#[launch]
fn rocket() -> _ {
    rocket::build().mount("/", routes![index, update_k])
}