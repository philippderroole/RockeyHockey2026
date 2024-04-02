/*     */ package rockyhockey.gui.mvc;
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
/*     */ public class Controller
/*     */   implements Runnable
/*     */ {
/*     */   public static final long GAME_TIME = 600000000000L;
/*     */   public static final int PLAYER = 0;
/*     */   public static final int BOT = 1;
/*     */   public static final int UNDEFINED = -1;
/*     */   private static Controller instance;
/*  25 */   private Gui gui = Gui.getInstance();
/*  26 */   private Audio audio = Audio.getInstance();
/*  27 */   private HardwareIO hardware = HardwareIO.getInstance();
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static Controller getInstance() {
/*  35 */     if (instance == null) {
/*  36 */       instance = new Controller();
/*     */     }
/*  38 */     return instance;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void start() {
/*  45 */     (new Thread(this)).start();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void run() {
/*  54 */     boolean isReseted = true;
/*  55 */     long timeRemaining = 600000000000L;
/*     */     
/*  57 */     int scorePlayer = 0;
/*  58 */     int scoreBot = 0;
/*  59 */     int lastGoal = -1;
/*  60 */     int highestRun = 0;
/*  61 */     int leader = -1;
/*     */     try {
/*     */       while (true) {
/*  64 */         if (this.gui.isPlayPressed() && isReseted) {
/*  65 */           isReseted = false;
/*  66 */           this.audio.playSound("prepare.wav");
/*  67 */           Thread.sleep(2000L);
/*  68 */           this.audio.startBackgroundSound();
/*  69 */           long timeAtStart = System.nanoTime();
/*  70 */           while (timeRemaining > 0L) {
/*  71 */             this.gui.setRemainingTime(timeRemaining);
/*     */             
/*  73 */             if (this.gui.isResetPressed()) {
/*  74 */               this.gui.reset();
/*  75 */               isReseted = true;
/*     */               
/*     */               break;
/*     */             } 
/*  79 */             if (this.hardware.isPlayerLsActive()) {
/*  80 */               scorePlayer++;
/*  81 */               this.gui.setPlayerScore(scorePlayer);
/*  82 */               if (lastGoal == 0) {
/*  83 */                 highestRun++;
/*     */               } else {
/*     */                 
/*  86 */                 highestRun = 1;
/*  87 */                 lastGoal = 0;
/*     */               } 
/*     */               
/*  90 */               if (scorePlayer >= 10) {
/*  91 */                 this.audio.playSound("winner.wav");
/*     */                 break;
/*     */               } 
/*  94 */               if (scorePlayer > scoreBot && (leader == 1 || leader == -1)) {
/*  95 */                 this.audio.playSound("takenlead.wav");
/*  96 */                 leader = 0;
/*     */               } else {
/*     */                 
/*  99 */                 this.audio.playScoreSound(highestRun, scorePlayer);
/*     */               }
/*     */             
/* 102 */             } else if (this.hardware.isBotLsActive()) {
/* 103 */               scoreBot++;
/* 104 */               this.gui.setBotScore(scoreBot);
/* 105 */               if (lastGoal == 1) {
/* 106 */                 highestRun++;
/*     */               } else {
/*     */                 
/* 109 */                 highestRun = 1;
/* 110 */                 lastGoal = 1;
/*     */               } 
/*     */               
/* 113 */               if (scoreBot >= 10) {
/* 114 */                 this.audio.playSound("lostmatch.wav");
/*     */                 break;
/*     */               } 
/* 117 */               if (scorePlayer <= scoreBot && leader == 0) {
/* 118 */                 this.audio.playSound("lostlead.wav");
/* 119 */                 leader = 1;
/*     */               } else {
/*     */                 
/* 122 */                 this.audio.playScoreSound(highestRun, scoreBot);
/*     */               } 
/*     */             } 
/* 125 */             timeRemaining = 600000000000L - System.nanoTime() - timeAtStart;
/* 126 */             Thread.sleep(2L);
/*     */           } 
/* 128 */           this.audio.stopBackgroundSound();
/*     */         } 
/* 130 */         if (this.gui.isResetPressed()) {
/* 131 */           this.gui.reset();
/* 132 */           this.hardware.resetOutput();
/* 133 */           isReseted = true;
/* 134 */           scoreBot = 0;
/* 135 */           scorePlayer = 0;
/*     */         } 
/*     */         
/* 138 */         Thread.sleep(2L);
/*     */       
/*     */       }
/*     */     
/*     */     }
/* 143 */     catch (InterruptedException e) {
/* 144 */       e.printStackTrace();
/*     */       return;
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /home/felix/Downloads/JavaGUI (Kopie).jar!/rockyhockey/gui/mvc/Controller.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */