/*     */ package rockyhockey.gui.mvc;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class Audio
/*     */ {
/*     */   private static Audio instance;
/*     */   private boolean soundEnabled = true;
/*  13 */   private volatile AudioThread backgroundMusicThread = null;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static Audio getInstance() {
/*  20 */     if (instance == null) {
/*  21 */       instance = new Audio();
/*     */     }
/*  23 */     return instance;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void playSound(String filename) {
/*  32 */     if (this.soundEnabled) {
/*  33 */       AudioThread.playSound(filename);
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void startBackgroundSound() {
/*  42 */     if (this.soundEnabled && 
/*  43 */       this.backgroundMusicThread == null) {
/*  44 */       this.backgroundMusicThread = AudioThread.playSound("backgroundsound.wav", true);
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void stopBackgroundSound() {
/*  53 */     if (this.backgroundMusicThread != null) {
/*  54 */       synchronized (this.backgroundMusicThread) {
/*  55 */         this.backgroundMusicThread.interrupt();
/*     */         
/*  57 */         this.backgroundMusicThread = null;
/*     */       } 
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void enableSound() {
/*  66 */     this.soundEnabled = true;
/*  67 */     startBackgroundSound();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void disableSound() {
/*  74 */     this.soundEnabled = false;
/*  75 */     stopBackgroundSound();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void playScoreSound(int run, int score) {
/*  86 */     switch (run) {
/*     */       case 3:
/*  88 */         playSound("dominating.wav");
/*     */         return;
/*     */       case 5:
/*  91 */         playSound("rampage.wav");
/*     */         return;
/*     */       case 7:
/*  94 */         playSound("unstoppable.wav");
/*     */         return;
/*     */       case 9:
/*  97 */         playSound("godlike.wav");
/*     */         return;
/*     */     } 
/* 100 */     playGoalSound(score);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void playGoalSound(int goal) {
/* 110 */     switch (goal) {
/*     */       case 1:
/* 112 */         playSound("one.wav");
/*     */         break;
/*     */       case 2:
/* 115 */         playSound("two.wav");
/*     */         break;
/*     */       case 3:
/* 118 */         playSound("three.wav");
/*     */         break;
/*     */       case 4:
/* 121 */         playSound("four.wav");
/*     */         break;
/*     */       case 5:
/* 124 */         playSound("five.wav");
/*     */         break;
/*     */       case 6:
/* 127 */         playSound("six.wav");
/*     */         break;
/*     */       case 7:
/* 130 */         playSound("seven.wav");
/*     */         break;
/*     */       case 8:
/* 133 */         playSound("eight.wav");
/*     */         break;
/*     */       case 9:
/* 136 */         playSound("nine.wav");
/*     */         break;
/*     */       case 10:
/* 139 */         playSound("ten.wav");
/*     */         break;
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/Audio.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */