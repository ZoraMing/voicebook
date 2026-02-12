
export interface LrcLine {
    time: number; // 秒
    text: string;
}

/**
 * 解析 LRC 歌词内容
 * 格式: [mm:ss.xx]歌词内容
 */
export function parseLrc(lrcContent: string): LrcLine[] {
    const lines = lrcContent.split('\n');
    const result: LrcLine[] = [];

    // 时间戳正则: [00:00.00] 或 [00:00]
    const timeReg = /\[(\d{2}):(\d{2})(\.\d{2,3})?\]/;

    for (const line of lines) {
        const match = line.match(timeReg);
        if (match) {
            const min = parseInt(match[1]);
            const sec = parseInt(match[2]);
            const ms = match[3] ? parseFloat(match[3]) : 0;

            const time = min * 60 + sec + ms;
            const text = line.replace(timeReg, '').trim();

            if (text) { // 忽略空行，除非需要占位
                result.push({ time, text });
            }
        }
    }

    return result.sort((a, b) => a.time - b.time);
}
