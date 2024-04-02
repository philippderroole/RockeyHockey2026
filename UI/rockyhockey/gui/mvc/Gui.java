/*     */ package rockyhockey.gui.mvc;
/*     */ 
/*     */ import java.awt.Color;
/*     */ import java.awt.Component;
/*     */ import java.awt.Dimension;
/*     */ import java.awt.Font;
/*     */ import java.awt.Graphics;
/*     */ import java.awt.Image;
/*     */ import java.awt.LayoutManager;
/*     */ import java.awt.Toolkit;
/*     */ import java.awt.event.ActionEvent;
/*     */ import java.awt.event.ActionListener;
/*     */ import javax.imageio.ImageIO;
/*     */ import javax.swing.ImageIcon;
/*     */ import javax.swing.JButton;
/*     */ import javax.swing.JFrame;
/*     */ import javax.swing.JLabel;
/*     */ import javax.swing.JPanel;
/*     */ import rockyhockey.gui.specialbuttons.IconButton;
/*     */ import rockyhockey.gui.specialbuttons.MuteButton;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class Gui
/*     */   extends JFrame
/*     */   implements ActionListener
/*     */ {
/*     */   private static final long serialVersionUID = 1L;
/*     */   private static Gui instance;
/*     */   private ImageIcon playIcon;
/*     */   private ImageIcon resetIcon;
/*     */   private ImageIcon closeIcon;
/*  38 */   private Image backgroundImage = null;
/*     */   
/*  40 */   private Color foreground = Color.red;
/*  41 */   private Color foregroundDefault = Color.white;
/*     */   private boolean playPressed;
/*     */   private boolean resetPressed;
/*     */   private boolean mutePressed;
/*     */   private boolean soundActive;
/*     */   private PanelWithBackground contentPanel;
/*     */   private JLabel playerLabel;
/*     */   private JLabel botLabel;
/*     */   private JLabel playerScoreLabel;
/*     */   private JLabel botScoreLabel;
/*     */   private JLabel scoreColon;
/*     */   private JLabel timeLabel;
/*     */   private IconButton playButton;
/*     */   private IconButton resetButton;
/*     */   private IconButton closeButton;
/*     */   private MuteButton muteButton;
/*     */   
/*     */   class PanelWithBackground
/*     */     extends JPanel
/*     */   {
/*     */     private static final long serialVersionUID = 1L;
/*     */     
/*     */     protected void paintComponent(Graphics g) {
/*  64 */       g.clearRect(0, 0, (getBounds()).width, (getBounds()).height);
/*  65 */       if (Gui.this.backgroundImage != null) {
/*  66 */         g.drawImage(Gui.this.backgroundImage, 0, 0, (getBounds()).width, (getBounds()).height, null);
/*     */       }
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static Gui getInstance() {
/*  91 */     if (instance == null) {
/*  92 */       instance = new Gui();
/*     */     }
/*  94 */     return instance;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private ImageIcon getImageIcon(String filename) throws Exception {
/* 105 */     return new ImageIcon(ImageIO.read(ResourceLoader.load("/img/" + filename)));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private Gui() {
/*     */     try {
/* 115 */       this.playIcon = getImageIcon("play.png");
/* 116 */       this.resetIcon = getImageIcon("replay.png");
/* 117 */       this.closeIcon = getImageIcon("close.png");
/* 118 */       ImageIcon backgroundImageIcon = getImageIcon("background.png");
/* 119 */       if (backgroundImageIcon != null) {
/* 120 */         this.backgroundImage = backgroundImageIcon.getImage();
/*     */       }
/* 122 */     } catch (Exception e) {
/* 123 */       e.printStackTrace();
/*     */     } 
/*     */     
/* 126 */     initGuiElements();
/* 127 */     addComponents();
/* 128 */     setBounds();
/*     */     
/* 130 */     this.soundActive = true;
/*     */     
/* 132 */     setVisible(true);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void addComponents() {
/* 139 */     setContentPane(this.contentPanel);
/*     */     
/* 141 */     this.contentPanel.add(this.playerLabel);
/* 142 */     this.contentPanel.add(this.botLabel);
/* 143 */     this.contentPanel.add(this.playerScoreLabel);
/* 144 */     this.contentPanel.add(this.scoreColon);
/* 145 */     this.contentPanel.add(this.botScoreLabel);
/* 146 */     this.contentPanel.add(this.timeLabel);
/* 147 */     this.contentPanel.add((Component)this.playButton);
/* 148 */     this.contentPanel.add((Component)this.resetButton);
/* 149 */     this.contentPanel.add((Component)this.closeButton);
/* 150 */     this.contentPanel.add((Component)this.muteButton);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setBounds() {
/* 157 */     Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
/*     */     
/* 159 */     int x = 0;
/* 160 */     int y = 0;
/* 161 */     int width = dim.width;
/* 162 */     int height = dim.height;
/*     */     
/* 164 */     setBounds(x, y, width, height);
/* 165 */     setBounds(x, y, width, height);
/* 166 */     this.contentPanel.setBounds(x, y, width, height);
/*     */     
/* 168 */     int eigth_of_width = width / 8;
/* 169 */     int eight_of_height = height / 8;
/*     */     
/* 171 */     this.closeButton.setBounds(width - eigth_of_width, 0, eigth_of_width, eight_of_height);
/* 172 */     this.muteButton.setBounds(width - 2 * eigth_of_width, 0, eigth_of_width, eight_of_height);
/* 173 */     this.playerLabel.setBounds(eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 174 */     this.botLabel.setBounds(width - 3 * eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 175 */     this.timeLabel.setBounds(3 * eigth_of_width, eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 176 */     this.playerScoreLabel.setBounds(eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 177 */     this.botScoreLabel.setBounds(width - 3 * eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 178 */     this.playButton.setBounds(eigth_of_width, 6 * eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 179 */     this.resetButton.setBounds(width - 3 * eigth_of_width, 6 * eight_of_height, 2 * eigth_of_width, eight_of_height);
/* 180 */     this.scoreColon.setBounds(3 * eigth_of_width, 3 * eight_of_height, 2 * eigth_of_width, eight_of_height);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void initGuiElements() {
/* 187 */     Font font = new Font("Arial", 1, 32);
/*     */     
/* 189 */     setLayout((LayoutManager)null);
/* 190 */     setUndecorated(true);
/* 191 */     setDefaultCloseOperation(3);
/*     */     
/* 193 */     this.contentPanel = new PanelWithBackground();
/* 194 */     this.contentPanel.setLayout((LayoutManager)null);
/*     */     
/* 196 */     this.playButton = new IconButton();
/* 197 */     this.playButton.addActionListener(this);
/*     */     
/* 199 */     this.resetButton = new IconButton();
/* 200 */     this.resetButton.addActionListener(this);
/*     */     
/* 202 */     this.closeButton = new IconButton();
/* 203 */     this.closeButton.addActionListener(this);
/*     */     
/* 205 */     this.muteButton = new MuteButton();
/* 206 */     this.muteButton.addActionListener(this);
/*     */     
/* 208 */     this.playerLabel = new JLabel();
/* 209 */     this.playerLabel.setHorizontalAlignment(0);
/* 210 */     this.playerLabel.setVerticalAlignment(0);
/* 211 */     this.playerLabel.setForeground(this.foreground);
/* 212 */     this.playerLabel.setFont(font);
/*     */     
/* 214 */     this.botLabel = new JLabel();
/* 215 */     this.botLabel.setHorizontalAlignment(0);
/* 216 */     this.botLabel.setForeground(this.foreground);
/* 217 */     this.botLabel.setFont(font);
/*     */     
/* 219 */     this.playerScoreLabel = new JLabel();
/* 220 */     this.playerScoreLabel.setHorizontalAlignment(0);
/* 221 */     this.playerScoreLabel.setForeground(this.foregroundDefault);
/* 222 */     this.playerScoreLabel.setFont(font);
/*     */     
/* 224 */     this.scoreColon = new JLabel(":");
/* 225 */     this.scoreColon.setFont(font);
/* 226 */     this.scoreColon.setHorizontalAlignment(0);
/* 227 */     this.scoreColon.setForeground(this.foregroundDefault);
/*     */     
/* 229 */     this.botScoreLabel = new JLabel();
/* 230 */     this.botScoreLabel.setHorizontalAlignment(0);
/* 231 */     this.botScoreLabel.setForeground(this.foregroundDefault);
/* 232 */     this.botScoreLabel.setFont(font);
/*     */     
/* 234 */     this.timeLabel = new JLabel();
/* 235 */     this.timeLabel.setHorizontalAlignment(0);
/* 236 */     this.timeLabel.setForeground(this.foregroundDefault);
/* 237 */     this.timeLabel.setFont(font);
/*     */     
/* 239 */     reset();
/*     */     
/* 241 */     this.playButton.setIcon(this.playIcon);
/* 242 */     this.closeButton.setIcon(this.closeIcon);
/* 243 */     this.resetButton.setIcon(this.resetIcon);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void reset() {
/* 250 */     this.playerLabel.setText("Player");
/* 251 */     this.botLabel.setText("Bot");
/* 252 */     this.playerScoreLabel.setText("0");
/* 253 */     this.botScoreLabel.setText("0");
/* 254 */     this.timeLabel.setText("10:00");
/* 255 */     this.timeLabel.setForeground(this.foregroundDefault);
/* 256 */     repaint();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isPlayPressed() {
/* 264 */     if (this.playPressed) {
/* 265 */       this.playPressed = false;
/* 266 */       return true;
/*     */     } 
/* 268 */     return false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isResetPressed() {
/* 276 */     if (this.resetPressed) {
/* 277 */       this.resetPressed = false;
/* 278 */       return true;
/*     */     } 
/* 280 */     return false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isMutePressed() {
/* 288 */     if (this.mutePressed) {
/* 289 */       this.mutePressed = false;
/* 290 */       return true;
/*     */     } 
/* 292 */     return false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPlayerScore(int score) {
/* 300 */     this.playerScoreLabel.setText(score);
/* 301 */     this.playerScoreLabel.repaint();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setBotScore(int score) {
/* 309 */     this.botScoreLabel.setText(score);
/* 310 */     this.botScoreLabel.repaint();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setRemainingTime(long countdownTime) {
/* 318 */     int time = (int)(countdownTime / 1000000000L);
/* 319 */     int min = time / 60;
/* 320 */     int sec = time % 60;
/* 321 */     this.timeLabel.setText(String.valueOf((min < 10) ? ("0" + min) : min) + ":" + ((sec < 10) ? ("0" + sec) : sec));
/* 322 */     if (min < 1) {
/* 323 */       this.timeLabel.setForeground(Color.red);
/*     */     }
/* 325 */     this.timeLabel.repaint();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void actionPerformed(ActionEvent event) {
/* 333 */     JButton sourceButton = (JButton)event.getSource();
/* 334 */     if (sourceButton == this.playButton) {
/* 335 */       this.playPressed = true;
/*     */     }
/* 337 */     else if (sourceButton == this.resetButton) {
/* 338 */       this.resetPressed = true;
/*     */     }
/* 340 */     else if (sourceButton == this.muteButton) {
/* 341 */       this.muteButton.toggleIcon();
/* 342 */       this.soundActive ^= 0x1;
/* 343 */       if (this.soundActive) {
/* 344 */         Audio.getInstance().enableSound();
/*     */       } else {
/*     */         
/* 347 */         Audio.getInstance().disableSound();
/*     */       } 
/* 349 */       this.mutePressed = true;
/*     */     }
/* 351 */     else if (sourceButton == this.closeButton) {
/* 352 */       System.exit(0);
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/Gui.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */