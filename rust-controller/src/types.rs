#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct Puck {
    pub position: Point,
    pub velocity: Point,
}

impl Point {
    pub fn distance_to(self, other: Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        (dx * dx + dy * dy).sqrt()
    }
}

#[derive(Debug, Clone, Copy)]
pub struct DetectionSnapshot {
    pub puck: Option<Point>,
    pub robot: Option<Point>,
    pub timestamp: std::time::Instant,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum MoveType {
    FastIntercept,
    SlowIntercept,
    Defend,
}

#[derive(Debug, Clone, Copy)]
pub struct MoveTarget {
    pub x: f64,
    pub y: f64,
    pub move_type: MoveType,
}
