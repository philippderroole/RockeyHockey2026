mod detector;
mod settings;
mod timed_detector;
mod virtual_coordinate_system;

pub use crate::puck_detector::virtual_coordinate_system::VirtualCoordinateSystem;
pub use detector::DetectionOutput;
pub use detector::PuckDetector;
use opencv::videoio::VideoCapture;
pub use timed_detector::TimedDetectionOutput;
pub use timed_detector::TimedFrameProcessing;
pub use timed_detector::TimedPuckDetector;

pub use settings::CropSettings;
pub use settings::DetectorSettings;
pub use settings::HsvThresholds;
pub use settings::ProcessingQuality;
pub use settings::RuntimeDetectorSettings;

pub trait DetectionPipeline {
    type CaptureOutput;
    type DetectOutput;
    type CombinedOutput;

    fn capture(&mut self, cam: &mut VideoCapture) -> Self::CaptureOutput;

    fn detect(&mut self) -> Self::DetectOutput;

    fn capture_and_detect(&mut self, cam: &mut VideoCapture) -> Self::CombinedOutput;
}
