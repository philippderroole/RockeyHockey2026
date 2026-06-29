package rockyhockey.gui.mvc;

public class Controller
        implements Runnable {
    public static final long GAME_TIME = 600000000000L;
    public static final int PLAYER = 0;
    public static final int BOT = 1;
    public static final int UNDEFINED = -1;
    private static Controller instance;
    private Gui gui = Gui.getInstance();
    private Audio audio = Audio.getInstance();
    private HardwareIO hardware = HardwareIO.getInstance();

    public static Controller getInstance() {
        if (instance == null) {
            instance = new Controller();
        }
        return instance;
    }

    public void start() {
        (new Thread(this)).start();
    }

    public void run() {
        boolean isReseted = true;
        long timeRemaining = 600000000000L;

        int scorePlayer = 0;
        int scoreBot = 0;
        int lastGoal = -1;
        int highestRun = 0;
        int leader = -1;
        try {
            while (true) {
                if (this.gui.isPlayPressed() && isReseted) {
                    isReseted = false;
                    this.audio.playSound("prepare.wav");
                    Thread.sleep(2000L);
                    this.audio.startBackgroundSound();
                    long timeAtStart = System.nanoTime();
                    while (timeRemaining > 0L) {
                        this.gui.setRemainingTime(timeRemaining);

                        if (this.gui.isResetPressed()) {
                            this.gui.reset();
                            isReseted = true;

                            break;
                        }
                        if (this.hardware.isPlayerLsActive()) {
                            scorePlayer++;
                            this.gui.setPlayerScore(scorePlayer);
                            if (lastGoal == 0) {
                                highestRun++;
                            } else {

                                highestRun = 1;
                                lastGoal = 0;
                            }

                            if (scorePlayer >= 10) {
                                this.audio.playSound("winner.wav");
                                break;
                            }
                            if (scorePlayer > scoreBot && (leader == 1 || leader == -1)) {
                                this.audio.playSound("takenlead.wav");
                                leader = 0;
                            } else {

                                this.audio.playScoreSound(highestRun, scorePlayer);
                            }

                        } else if (this.hardware.isBotLsActive()) {
                            scoreBot++;
                            this.gui.setBotScore(scoreBot);
                            if (lastGoal == 1) {
                                highestRun++;
                            } else {

                                highestRun = 1;
                                lastGoal = 1;
                            }

                            if (scoreBot >= 10) {
                                this.audio.playSound("lostmatch.wav");
                                break;
                            }
                            if (scorePlayer <= scoreBot && leader == 0) {
                                this.audio.playSound("lostlead.wav");
                                leader = 1;
                            } else {

                                this.audio.playScoreSound(highestRun, scoreBot);
                            }
                        }
                        timeRemaining = 600000000000L - (System.nanoTime() - timeAtStart);
                        Thread.sleep(2L);
                    }
                    this.audio.stopBackgroundSound();
                }
                if (this.gui.isResetPressed()) {
                    this.gui.reset();
                    this.hardware.resetOutput();
                    isReseted = true;
                    scoreBot = 0;
                    scorePlayer = 0;
                }

                Thread.sleep(2L);

            }

        } catch (InterruptedException e) {
            e.printStackTrace();
            return;
        }
    }
}