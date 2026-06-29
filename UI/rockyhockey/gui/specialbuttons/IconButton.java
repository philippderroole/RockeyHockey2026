package rockyhockey.gui.specialbuttons;

import javax.swing.ImageIcon;
import javax.swing.JButton;

public class IconButton
        extends JButton {
    private static final long serialVersionUID = 1L;

    public IconButton(ImageIcon icon) {
        setOpaque(false);
        setContentAreaFilled(false);
        setBorderPainted(false);
        setIcon(icon);
        setFocusPainted(false);
    }

    public IconButton() {
        setOpaque(false);
        setContentAreaFilled(false);
        setBorderPainted(false);
        setFocusPainted(false);
    }
}