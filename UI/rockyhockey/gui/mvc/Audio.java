package rockyhockey.gui.mvc;

public class Audio {
    private static Audio instance;
    private boolean soundEnabled = true;
    private volatile AudioThread backgroundMusicThread = null;

    public static Audio getInstance() {
        if (instance == null) {
            instance = new Audio();
        }
        return instance;
    }

    public void playSound(String filename) {
        if (this.soundEnabled) {
            AudioThread.playSound(filename);
        }
    }

    public void startBackgroundSound() {
        if (this.soundEnabled &&
                this.backgroundMusicThread == null) {
            this.backgroundMusicThread = AudioThread.playSound("backgroundsound.wav", true);
        }
    }

    public void stopBackgroundSound() {
        if (this.backgroundMusicThread != null) {
            synchronized (this.backgroundMusicThread) {
                this.backgroundMusicThread.interrupt();

                this.backgroundMusicThread = null;
            }
        }
    }

    public void enableSound() {
        this.soundEnabled = true;
        startBackgroundSound();
    }

    public void disableSound() {
        this.soundEnabled = false;
        stopBackgroundSound();
    }

    public void playScoreSound(int run, int score) {
        switch (run) {
            case 3:
                playSound("dominating.wav");
                return;
            case 5:
                playSound("rampage.wav");
                return;
            case 7:
                playSound("unstoppable.wav");
                return;
            case 9:
                playSound("godlike.wav");
                return;
        }
        playGoalSound(score);
    }

    public void playGoalSound(int goal) {
        switch (goal) {
            case 1:
                playSound("one.wav");
                break;
            case 2:
                playSound("two.wav");
                break;
            case 3:
                playSound("three.wav");
                break;
            case 4:
                playSound("four.wav");
                break;
            case 5:
                playSound("five.wav");
                break;
            case 6:
                playSound("six.wav");
                break;
            case 7:
                playSound("seven.wav");
                break;
            case 8:
                playSound("eight.wav");
                break;
            case 9:
                playSound("nine.wav");
                break;
            case 10:
                playSound("ten.wav");
                break;
        }
    }
}