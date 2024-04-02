/*    */ package rockyhockey.gui.specialbuttons;
/*    */ 
/*    */ import java.io.IOException;
/*    */ import javax.imageio.ImageIO;
/*    */ import javax.swing.ImageIcon;
/*    */ import javax.swing.JButton;
/*    */ import rockyhockey.gui.mvc.ResourceLoader;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class MuteButton
/*    */   extends JButton
/*    */ {
/*    */   private static final long serialVersionUID = 1L;
/*    */   private static ImageIcon mutedIcon;
/*    */   private static ImageIcon unmutedIcon;
/*    */   private boolean iconNotNull;
/*    */   private boolean defaultIcon;
/*    */   
/*    */   static {
/*    */     try {
/* 28 */       mutedIcon = new ImageIcon(ImageIO.read(ResourceLoader.load("/img/mute.png")));
/* 29 */       unmutedIcon = new ImageIcon(ImageIO.read(ResourceLoader.load("/img/sound.png")));
/*    */     }
/* 31 */     catch (IOException e) {
/* 32 */       e.printStackTrace();
/*    */     } 
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public MuteButton() {
/* 43 */     this.defaultIcon = true;
/* 44 */     setOpaque(false);
/* 45 */     setContentAreaFilled(false);
/* 46 */     setBorderPainted(false);
/* 47 */     setFocusPainted(false);
/* 48 */     this.iconNotNull = (mutedIcon != null && unmutedIcon != null);
/* 49 */     if (this.iconNotNull) {
/* 50 */       setIcon(unmutedIcon);
/*    */     }
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void toggleIcon() {
/* 58 */     if (this.iconNotNull) {
/* 59 */       this.defaultIcon ^= 0x1;
/* 60 */       setIcon(this.defaultIcon ? unmutedIcon : mutedIcon);
/* 61 */       repaint();
/*    */     } 
/*    */   }
/*    */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/specialbuttons/MuteButton.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */