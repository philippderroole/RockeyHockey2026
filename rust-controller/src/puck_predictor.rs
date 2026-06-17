use crate::types::Point;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BoardDimensions {
    pub width: f64,
    pub height: f64,
}

impl BoardDimensions {
    pub const fn new(width: f64, height: f64) -> Self {
        Self { width, height }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct PuckPredictor {
    board: BoardDimensions,
    puck_radius: f64,
    _max_bounces: usize,
}

impl PuckPredictor {
    pub const fn new(board: BoardDimensions, puck_radius: f64, max_bounces: usize) -> Self {
        Self {
            board,
            puck_radius,
            _max_bounces: max_bounces,
        }
    }

    pub fn predict(&self, position: Point, velocity: Point, time_seconds: f64) -> Option<Point> {
        if !position.x.is_finite()
            || !position.y.is_finite()
            || !velocity.x.is_finite()
            || !velocity.y.is_finite()
            || !time_seconds.is_finite()
            || time_seconds < 0.0
        {
            return None;
        }

        let x_bounds = self.axis_bounds(self.board.width)?;
        let y_bounds = self.axis_bounds(self.board.height)?;

        Some(Point {
            x: reflect_coordinate(position.x, velocity.x, time_seconds, x_bounds.0, x_bounds.1),
            y: reflect_coordinate(position.y, velocity.y, time_seconds, y_bounds.0, y_bounds.1),
        })
    }

    fn axis_bounds(&self, dimension: f64) -> Option<(f64, f64)> {
        if !dimension.is_finite() {
            return None;
        }

        let min = self.puck_radius;
        let max = dimension - self.puck_radius;
        if max < min {
            return None;
        }

        Some((min, max))
    }
}

fn reflect_coordinate(position: f64, velocity: f64, time_seconds: f64, min: f64, max: f64) -> f64 {
    let span = max - min;
    if span <= 0.0 {
        return min;
    }

    let travel = position + velocity * time_seconds;
    let relative = (travel - min).rem_euclid(span * 2.0);
    if relative <= span {
        min + relative
    } else {
        max - (relative - span)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn predicts_straight_line_without_bounce() {
        let predictor = PuckPredictor::new(BoardDimensions::new(400.0, 300.0), 10.0, 2);

        let predicted = predictor
            .predict(Point { x: 100.0, y: 50.0 }, Point { x: 20.0, y: 10.0 }, 2.0)
            .expect("prediction should succeed");

        assert_eq!(predicted.x, 140.0);
        assert_eq!(predicted.y, 70.0);
    }

    #[test]
    fn predicts_bounce_on_right_wall() {
        let predictor = PuckPredictor::new(BoardDimensions::new(400.0, 300.0), 10.0, 2);

        let predicted = predictor
            .predict(Point { x: 360.0, y: 120.0 }, Point { x: 30.0, y: 0.0 }, 2.0)
            .expect("prediction should succeed");

        assert_eq!(predicted.x, 360.0);
        assert_eq!(predicted.y, 120.0);
    }

    #[test]
    fn honors_custom_board_size() {
        let predictor = PuckPredictor::new(BoardDimensions::new(200.0, 100.0), 5.0, 2);

        let predicted = predictor
            .predict(Point { x: 30.0, y: 30.0 }, Point { x: -20.0, y: 10.0 }, 1.0)
            .expect("prediction should succeed");

        assert_eq!(predicted.x, 10.0);
        assert_eq!(predicted.y, 40.0);
    }
}
