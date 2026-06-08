use opencv::core::{Mat, Point, Rect, Scalar, Vector};
use opencv::imgproc::{self, FONT_HERSHEY_SIMPLEX, LINE_8};
use opencv::{imgcodecs, prelude::VectorToVec};

use crate::puck_detector::{RuntimeDetectorSettings, TimedDetectionOutput};

pub(super) fn draw_debug_detection(
    image: &Mat,
    output_data: &TimedDetectionOutput,
    runtime_settings: &RuntimeDetectorSettings,
) -> opencv::Result<Mat> {
    let mut output = image.clone();

    if let Some(result) = output_data.inner.as_ref() {
        for detection in result.iter() {
            if let Some(point) = detection.detection {
                let label = runtime_settings.target_name(detection.target_index);
                draw_detection_label(
                    &mut output,
                    point,
                    &label,
                    detection_color(detection.target_index),
                )?;
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

fn draw_detection_label(
    image: &mut Mat,
    point: Point,
    label: &str,
    color: Scalar,
) -> opencv::Result<()> {
    let mut baseline = 0;
    let text_size = imgproc::get_text_size(label, FONT_HERSHEY_SIMPLEX, 0.45, 1, &mut baseline)?;
    let padding_x = 4;
    let padding_y = 3;

    let mut label_x = point.x - (text_size.width / 2);
    let mut label_y = point.y - 14;
    label_x = label_x.max(0);
    label_y = label_y.max(text_size.height + padding_y);

    let rect_x = label_x.saturating_sub(padding_x);
    let rect_y = (label_y - text_size.height - padding_y).max(0);
    let rect = Rect::new(
        rect_x,
        rect_y,
        text_size.width + padding_x * 2,
        text_size.height + baseline + padding_y * 2,
    );

    imgproc::rectangle(
        image,
        rect,
        Scalar::new(255.0, 255.0, 255.0, 0.0),
        -1,
        LINE_8,
        0,
    )?;
    imgproc::rectangle(image, rect, color, 1, LINE_8, 0)?;
    imgproc::put_text(
        image,
        label,
        Point::new(label_x, label_y),
        FONT_HERSHEY_SIMPLEX,
        0.45,
        Scalar::new(25.0, 38.0, 33.0, 0.0),
        1,
        LINE_8,
        false,
    )?;

    Ok(())
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
