use opencv::core::Scalar;
use opencv::imgproc::{self, LINE_8};
use opencv::{
    core::{Mat, Vector},
    imgcodecs,
    prelude::VectorToVec,
};

use crate::puck_detector::TimedDetectionOutput;

pub(super) fn draw_debug_detection(
    image: &Mat,
    output_data: &TimedDetectionOutput,
) -> opencv::Result<Mat> {
    let mut output = image.clone();

    if let Some(result) = output_data.inner.as_ref() {
        for detection in result.iter() {
            if let Some(point) = detection.detection {
                imgproc::circle(
                    &mut output,
                    point,
                    10,
                    detection_color(detection.target_index),
                    2,
                    LINE_8,
                    0,
                )?;
            }
        }
    }

    Ok(output)
}

fn detection_color(target_index: usize) -> Scalar {
    match target_index % 5 {
        0 => Scalar::new(0.0, 0.0, 255.0, 0.0),
        1 => Scalar::new(0.0, 255.0, 0.0, 0.0),
        2 => Scalar::new(255.0, 0.0, 0.0, 0.0),
        3 => Scalar::new(0.0, 255.0, 255.0, 0.0),
        _ => Scalar::new(255.0, 0.0, 255.0, 0.0),
    }
}

pub(super) fn encode_jpeg(image: &Mat) -> opencv::Result<Vec<u8>> {
    let mut encoded = Vector::<u8>::new();
    let mut params = Vector::<i32>::new();
    params.push(imgcodecs::IMWRITE_JPEG_QUALITY);
    params.push(80);
    imgcodecs::imencode(".jpg", image, &mut encoded, &params)?;
    Ok(encoded.to_vec())
}
