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
        if result.detection.is_none() {
            return Ok(output);
        }

        imgproc::circle(
            &mut output,
            result.detection.unwrap(),
            10,
            Scalar::new(0.0, 0.0, 255.0, 0.0),
            2,
            LINE_8,
            0,
        )?;
    }

    Ok(output)
}

pub(super) fn encode_jpeg(image: &Mat) -> opencv::Result<Vec<u8>> {
    let mut encoded = Vector::<u8>::new();
    let mut params = Vector::<i32>::new();
    params.push(imgcodecs::IMWRITE_JPEG_QUALITY);
    params.push(80);
    imgcodecs::imencode(".jpg", image, &mut encoded, &params)?;
    Ok(encoded.to_vec())
}
