package rockyhockey.gui.specialbuttons;

import java.io.IOException;
import javax.imageio.ImageIO;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import rockyhockey.gui.mvc.ResourceLoader;

public class MuteButton
        extends JButton {
    private static final long serialVersionUID = 1L;
    private static ImageIcon mutedIcon;
    private static ImageIcon unmutedIcon;
    private boolean iconNotNull;
    private boolean defaultIcon;

    static {
        try {
            mutedIcon = new ImageIcon(ImageIO.read(ResourceLoader.load("/img/mute.png")));
            unmutedIcon = new ImageIcon(ImageIO.read(ResourceLoader.load("/img/sound.png")));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public MuteButton() {
        this.defaultIcon = true;
        setOpaque(false);
        setContentAreaFilled(false);
        setBorderPainted(false);
        setFocusPainted(false);
        this.iconNotNull = (mutedIcon != null && unmutedIcon != null);
        if (this.iconNotNull) {
            setIcon(unmutedIcon);
        }
    }

    public void toggleIcon() {
        if (this.iconNotNull) {
            this.defaultIcon = !defaultIcon;
            setIcon(this.defaultIcon ? unmutedIcon : mutedIcon);
            repaint();
        }
    }
}