package rockyhockey.gui.mvc;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.LayoutManager;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.imageio.ImageIO;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import rockyhockey.gui.specialbuttons.IconButton;
import rockyhockey.gui.specialbuttons.MuteButton;

public class Gui
        extends JFrame
        implements ActionListener {
    private static final long serialVersionUID = 1L;
    private static Gui instance;
    private ImageIcon playIcon;
    private ImageIcon resetIcon;
    private ImageIcon closeIcon;
    private Image backgroundImage = null;

    private Color foreground = Color.red;
    private Color foregroundDefault = Color.white;
    private boolean playPressed;
    private boolean resetPressed;
    private boolean mutePressed;
    private boolean soundActive;
    private PanelWithBackground contentPanel;
    private JLabel playerLabel;
    private JLabel botLabel;
    private JLabel playerScoreLabel;
    private JLabel botScoreLabel;
    private JLabel scoreColon;
    private JLabel timeLabel;
    private IconButton playButton;
    private IconButton resetButton;
    private IconButton closeButton;
    private MuteButton muteButton;

    class PanelWithBackground
            extends JPanel {
        private static final long serialVersionUID = 1L;

        protected void paintComponent(Graphics g) {
            g.clearRect(0, 0, (getBounds()).width, (getBounds()).height);
            if (Gui.this.backgroundImage != null) {
                g.drawImage(Gui.this.backgroundImage, 0, 0, (getBounds()).width, (getBounds()).height, null);
            }
        }
    }

    public static Gui getInstance() {
        if (instance == null) {
            instance = new Gui();
        }
        return instance;
    }

    private ImageIcon getImageIcon(String filename) throws Exception {
        return new ImageIcon(ImageIO.read(ResourceLoader.load("/img/" + filename)));
    }

    private Gui() {
        try {
            this.playIcon = getImageIcon("play.png");
            this.resetIcon = getImageIcon("replay.png");
            this.closeIcon = getImageIcon("close.png");
            ImageIcon backgroundImageIcon = getImageIcon("background.png");
            if (backgroundImageIcon != null) {
                this.backgroundImage = backgroundImageIcon.getImage();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        initGuiElements();
        addComponents();
        setBounds();

        this.soundActive = true;

        setVisible(true);
    }

    private void addComponents() {
        setContentPane(this.contentPanel);

        this.contentPanel.add(this.playerLabel);
        this.contentPanel.add(this.botLabel);
        this.contentPanel.add(this.playerScoreLabel);
        this.contentPanel.add(this.scoreColon);
        this.contentPanel.add(this.botScoreLabel);
        this.contentPanel.add(this.timeLabel);
        this.contentPanel.add((Component) this.playButton);
        this.contentPanel.add((Component) this.resetButton);
        this.contentPanel.add((Component) this.closeButton);
        this.contentPanel.add((Component) this.muteButton);
    }

    public void setBounds() {
        Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();

        int x = 0;
        int y = 0;
        int width = dim.width;
        int height = dim.height;

        setBounds(x, y, width, height);
        setBounds(x, y, width, height);
        this.contentPanel.setBounds(x, y, width, height);

        int eigth_of_width = width / 8;
        int eight_of_height = height / 8;

        this.closeButton.setBounds(width - eigth_of_width, 0, eigth_of_width, eight_of_height);
        this.muteButton.setBounds(width - 2 * eigth_of_width, 0, eigth_of_width, eight_of_height);
        this.playerLabel.setBounds(eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
        this.botLabel.setBounds(width - 3 * eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
        this.timeLabel.setBounds(3 * eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
        this.playerScoreLabel.setBounds(eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width, eight_of_height);
        this.botScoreLabel.setBounds(width - 3 * eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width,
                eight_of_height);
        this.playButton.setBounds(eigth_of_width, 6 * eight_of_height, 2 * eigth_of_width, eight_of_height);
        this.resetButton.setBounds(width - 3 * eigth_of_width, 6 * eight_of_height, 2 * eigth_of_width,
                eight_of_height);
        this.scoreColon.setBounds(3 * eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width, eight_of_height);
    }

    private void initGuiElements() {
        Font font = new Font("Arial", 1, 32);

        setLayout((LayoutManager) null);
        setUndecorated(true);
        setDefaultCloseOperation(3);

        this.contentPanel = new PanelWithBackground();
        this.contentPanel.setLayout((LayoutManager) null);

        this.playButton = new IconButton();
        this.playButton.addActionListener(this);

        this.resetButton = new IconButton();
        this.resetButton.addActionListener(this);

        this.closeButton = new IconButton();
        this.closeButton.addActionListener(this);

        this.muteButton = new MuteButton();
        this.muteButton.addActionListener(this);

        this.playerLabel = new JLabel();
        this.playerLabel.setHorizontalAlignment(0);
        this.playerLabel.setVerticalAlignment(0);
        this.playerLabel.setForeground(this.foreground);
        this.playerLabel.setFont(font);

        this.botLabel = new JLabel();
        this.botLabel.setHorizontalAlignment(0);
        this.botLabel.setForeground(this.foreground);
        this.botLabel.setFont(font);

        this.playerScoreLabel = new JLabel();
        this.playerScoreLabel.setHorizontalAlignment(0);
        this.playerScoreLabel.setForeground(this.foregroundDefault);
        this.playerScoreLabel.setFont(font);

        this.scoreColon = new JLabel(":");
        this.scoreColon.setFont(font);
        this.scoreColon.setHorizontalAlignment(0);
        this.scoreColon.setForeground(this.foregroundDefault);

        this.botScoreLabel = new JLabel();
        this.botScoreLabel.setHorizontalAlignment(0);
        this.botScoreLabel.setForeground(this.foregroundDefault);
        this.botScoreLabel.setFont(font);

        this.timeLabel = new JLabel();
        this.timeLabel.setHorizontalAlignment(0);
        this.timeLabel.setForeground(this.foregroundDefault);
        this.timeLabel.setFont(font);

        reset();

        this.playButton.setIcon(this.playIcon);
        this.closeButton.setIcon(this.closeIcon);
        this.resetButton.setIcon(this.resetIcon);
    }

    public void reset() {
        this.playerLabel.setText("Player");
        this.botLabel.setText("Bot");
        this.playerScoreLabel.setText("0");
        this.botScoreLabel.setText("0");
        this.timeLabel.setText("10:00");
        this.timeLabel.setForeground(this.foregroundDefault);
        repaint();
    }

    public boolean isPlayPressed() {
        if (this.playPressed) {
            this.playPressed = false;
            return true;
        }
        return false;
    }

    public boolean isResetPressed() {
        if (this.resetPressed) {
            this.resetPressed = false;
            return true;
        }
        return false;
    }

    public boolean isMutePressed() {
        if (this.mutePressed) {
            this.mutePressed = false;
            return true;
        }
        return false;
    }

    public void setPlayerScore(int score) {
        this.playerScoreLabel.setText(Integer.toString(score));
        this.playerScoreLabel.repaint();
    }

    public void setBotScore(int score) {
        this.botScoreLabel.setText(Integer.toString(score));
        this.botScoreLabel.repaint();
    }

    public void setRemainingTime(long countdownTime) {
        int time = (int) (countdownTime / 1000000000L);
        int min = time / 60;
        int sec = time % 60;
        this.timeLabel.setText(String.valueOf((min < 10) ? ("0" + min) : min) + ":" + ((sec < 10) ? ("0" + sec) : sec));
        if (min < 1) {
            this.timeLabel.setForeground(Color.red);
        }
        this.timeLabel.repaint();
    }

    public void actionPerformed(ActionEvent event) {
        JButton sourceButton = (JButton) event.getSource();
        if (sourceButton == this.playButton) {
            this.playPressed = true;
        } else if (sourceButton == this.resetButton) {
            this.resetPressed = true;
        } else if (sourceButton == this.muteButton) {
            this.muteButton.toggleIcon();
            this.soundActive = !soundActive;
            if (this.soundActive) {
                Audio.getInstance().enableSound();
            } else {

                Audio.getInstance().disableSound();
            }
            this.mutePressed = true;
        } else if (sourceButton == this.closeButton) {
            System.exit(0);
        }
    }
}