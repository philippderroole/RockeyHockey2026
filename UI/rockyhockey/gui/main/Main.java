package rockyhockey.gui.main;

import rockyhockey.gui.mvc.Controller;

public class Main {
    public static void main(String[] args) {
        Controller controller = Controller.getInstance();
        controller.start();
    }
}