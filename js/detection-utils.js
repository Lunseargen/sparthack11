// Detection utilities for client-side logs, compaction, and correction
// Stores logs locally to replace server endpoints (except vision processing)

(() => {
    const DETECTIONS_KEY = 'detectionsLog';
    const COMPACTED_KEY = 'compactedLog';
    const CORRECTED_KEY = 'correctedLog';

    const COMMON_WORDS = new Set([
        'a', 'i',
        'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'hi', 'if', 'in',
        'is', 'it', 'me', 'my', 'no', 'of', 'ok', 'on', 'or', 'so', 'to', 'up',
        'us', 'we',
        'all', 'and', 'any', 'are', 'ask', 'bad', 'big', 'boy', 'but', 'buy',
        'can', 'car', 'cat', 'dad', 'day', 'did', 'dog', 'eat', 'end', 'eye',
        'far', 'few', 'for', 'fun', 'get', 'god', 'got', 'guy', 'had', 'has',
        'her', 'him', 'his', 'hot', 'how', 'its', 'job', 'joy', 'just', 'keep',
        'key', 'kid', 'let', 'lot', 'man', 'may', 'mom', 'mrs', 'new', 'not',
        'now', 'off', 'old', 'one', 'our', 'out', 'own', 'pay', 'put', 'ran',
        'run', 'sad', 'sat', 'saw', 'say', 'see', 'set', 'she', 'sit', 'six',
        'son', 'ten', 'the', 'too', 'top', 'try', 'two', 'use', 'war', 'was',
        'way', 'who', 'why', 'win', 'won', 'yes', 'yet', 'you',
        'able', 'also', 'back', 'ball', 'bank', 'been', 'best', 'bill', 'body',
        'book', 'both', 'call', 'came', 'come', 'cool', 'city', 'dark', 'data',
        'deal', 'does', 'done', 'door', 'down', 'each', 'east', 'easy', 'else',
        'even', 'ever', 'face', 'fact', 'fall', 'feel', 'find', 'fire', 'food',
        'four', 'free', 'from', 'full', 'game', 'gave', 'girl', 'give', 'glad',
        'goes', 'gone', 'good', 'great', 'grow', 'hair', 'half', 'hand', 'hard',
        'have', 'head', 'hear', 'help', 'here', 'high', 'hold', 'home', 'hope',
        'hour', 'idea', 'into', 'just', 'keep', 'kind', 'knew', 'know', 'land',
        'last', 'late', 'left', 'less', 'life', 'like', 'line', 'live', 'long',
        'look', 'love', 'made', 'main', 'make', 'many', 'meet', 'mind', 'more',
        'most', 'move', 'much', 'must', 'name', 'near', 'need', 'next', 'nice',
        'none', 'once', 'only', 'open', 'over', 'paid', 'part', 'pass', 'past',
        'pick', 'plan', 'play', 'read', 'real', 'rest', 'right', 'road', 'room',
        'safe', 'said', 'same', 'save', 'seen', 'self', 'send', 'show', 'side',
        'sign', 'size', 'some', 'soon', 'stay', 'stop', 'such', 'sure', 'take',
        'talk', 'tell', 'text', 'than', 'that', 'them', 'then', 'they', 'this',
        'thus', 'time', 'told', 'took', 'tree', 'true', 'turn', 'type', 'upon',
        'used', 'user', 'very', 'view', 'wait', 'walk', 'wall', 'want', 'week',
        'well', 'went', 'were', 'west', 'what', 'when', 'will', 'with', 'word',
        'work', 'year', 'your',
        'about', 'above', 'after', 'again', 'being', 'below', 'black', 'bring',
        'cause', 'child', 'clear', 'close', 'could', 'doing', 'early', 'every',
        'field', 'first', 'found', 'front', 'given', 'going', 'great', 'green',
        'group', 'happy', 'heard', 'heart', 'hello', 'house', 'human', 'known',
        'large', 'later', 'learn', 'leave', 'level', 'light', 'little', 'local',
        'might', 'money', 'month', 'never', 'night', 'often', 'order', 'other',
        'party', 'peace', 'place', 'plant', 'point', 'power', 'press', 'quite',
        'ready', 'right', 'river', 'round', 'seems', 'shall', 'short', 'shown',
        'since', 'small', 'sorry', 'sound', 'south', 'space', 'start', 'state',
        'still', 'study', 'table', 'taken', 'thank', 'thanks', 'their', 'there',
        'these', 'thing', 'think', 'third', 'those', 'three', 'today', 'under',
        'until', 'using', 'value', 'voice', 'watch', 'water', 'white', 'whole',
        'woman', 'women', 'world', 'would', 'write', 'wrong', 'young',
        'always', 'around', 'become', 'before', 'better', 'called', 'change',
        'coming', 'enough', 'family', 'friend', 'having', 'itself', 'little',
        'making', 'matter', 'minute', 'moment', 'mother', 'number', 'people',
        'person', 'please', 'rather', 'really', 'reason', 'school', 'should',
        'simple', 'social', 'system', 'things', 'though', 'together', 'toward',
        'wanted', 'without', 'working', 'because', 'between', 'brought', 'country',
        'during', 'example', 'father', 'general', 'getting', 'government', 'however',
        'looking', 'morning', 'nothing', 'problem', 'program', 'several', 'something',
        'special', 'started', 'through', 'understand', 'whether', 'another'
    ]);

    const WORDS_BY_LEN = (() => {
        const map = new Map();
        for (const w of COMMON_WORDS) {
            const len = w.length;
            if (!map.has(len)) map.set(len, new Set());
            map.get(len).add(w);
        }
        return map;
    })();

    const SEPARATORS = new Set(['sp', 'space', '_', 'fn', 'none']);

    const safeParse = (value, fallback) => {
        try {
            const parsed = JSON.parse(value);
            return parsed ?? fallback;
        } catch (err) {
            return fallback;
        }
    };

    const loadDetections = () => {
        const raw = window.localStorage.getItem(DETECTIONS_KEY);
        const parsed = safeParse(raw || '[]', []);
        return Array.isArray(parsed) ? parsed : [];
    };

    const saveDetections = (data) => {
        const payload = Array.isArray(data) ? data : [];
        window.localStorage.setItem(DETECTIONS_KEY, JSON.stringify(payload));
    };

    const clearDetections = () => {
        window.localStorage.setItem(DETECTIONS_KEY, '[]');
        window.localStorage.setItem(COMPACTED_KEY, '[]');
        window.localStorage.setItem(CORRECTED_KEY, '[]');
    };

    const extractFrameLabel = (row) => {
        if (row && typeof row === 'object' && !Array.isArray(row)) {
            const frame = row.frame_count ?? row.frame;
            const label = row.label;
            return [frame, label];
        }
        if (Array.isArray(row) && row.length >= 3) {
            return [row[0], row[2]];
        }
        return [null, null];
    };

    const compactDetectionRanges = (detections) => {
        const compacted = [];
        let currentLabel = null;
        let rangeStart = null;
        let rangeEnd = null;

        for (const row of detections || []) {
            let [frame, label] = extractFrameLabel(row);
            if (frame == null || label == null) continue;

            const frameNum = parseInt(frame, 10);
            if (!Number.isFinite(frameNum)) continue;

            if (currentLabel === null) {
                currentLabel = label;
                rangeStart = frameNum;
                rangeEnd = frameNum;
                continue;
            }

            if (label === currentLabel) {
                if (frameNum > rangeEnd) rangeEnd = frameNum;
                continue;
            }

            compacted.push({ frameRange: `${rangeStart}-${rangeEnd}`, label: currentLabel });
            currentLabel = label;
            rangeStart = frameNum;
            rangeEnd = frameNum;
        }

        if (currentLabel !== null) {
            compacted.push({ frameRange: `${rangeStart}-${rangeEnd}`, label: currentLabel });
        }

        window.localStorage.setItem(COMPACTED_KEY, JSON.stringify(compacted));
        return compacted;
    };

    const extractWordsFromCompacted = (compacted) => {
        const words = [];
        let current = [];
        let wordStart = null;
        let wordEnd = null;

        for (const entry of compacted || []) {
            const label = entry?.label;
            const frameRange = entry?.frameRange;
            if (!label || !frameRange) continue;

            const [startStr, endStr] = frameRange.split('-', 2);
            const startFrame = parseInt(startStr, 10);
            const endFrame = parseInt(endStr, 10);
            if (!Number.isFinite(startFrame) || !Number.isFinite(endFrame)) continue;

            if (SEPARATORS.has(label)) {
                if (current.length) {
                    words.push({ frameRange: `${wordStart}-${wordEnd}`, raw: current.join('') });
                    current = [];
                    wordStart = null;
                    wordEnd = null;
                }
                continue;
            }

            if (wordStart === null) wordStart = startFrame;
            wordEnd = endFrame;
            current.push(label);
        }

        if (current.length) {
            words.push({ frameRange: `${wordStart}-${wordEnd}`, raw: current.join('') });
        }

        return words;
    };

    const levenshtein = (s1, s2) => {
        if (s1.length < s2.length) [s1, s2] = [s2, s1];
        if (!s2.length) return s1.length;

        let prevRow = Array.from({ length: s2.length + 1 }, (_, i) => i);
        for (let i = 0; i < s1.length; i++) {
            const c1 = s1[i];
            const currRow = [i + 1];
            for (let j = 0; j < s2.length; j++) {
                const c2 = s2[j];
                const insertions = prevRow[j + 1] + 1;
                const deletions = currRow[j] + 1;
                const substitutions = prevRow[j] + (c1 !== c2 ? 1 : 0);
                currRow.push(Math.min(insertions, deletions, substitutions));
            }
            prevRow = currRow;
        }
        return prevRow[prevRow.length - 1];
    };

    const matchWord = (raw, maxDistance = 2) => {
        const rawLower = raw.toLowerCase();
        const rawLen = rawLower.length;

        if (COMMON_WORDS.has(rawLower)) return rawLower;

        let bestMatch = null;
        let bestDist = maxDistance + 1;

        for (let length = Math.max(1, rawLen - maxDistance); length <= rawLen + maxDistance; length++) {
            const candidates = WORDS_BY_LEN.get(length);
            if (!candidates) continue;
            for (const word of candidates) {
                const dist = levenshtein(rawLower, word);
                if (dist < bestDist) {
                    bestDist = dist;
                    bestMatch = word;
                }
                if (dist === 0) return word;
            }
        }

        if (bestMatch && bestDist <= maxDistance) return bestMatch;
        return raw;
    };

    const generateCorrectedLog = (detections) => {
        const compacted = compactDetectionRanges(detections);
        const wordEntries = extractWordsFromCompacted(compacted);
        const corrected = [];

        for (const word of wordEntries) {
            const raw = word?.raw || '';
            if (!raw) continue;
            const matched = matchWord(raw);
            corrected.push({ frame: word.frameRange, string: matched });
        }

        window.localStorage.setItem(CORRECTED_KEY, JSON.stringify(corrected));
        return corrected;
    };

    const getLogs = () => {
        const detections = loadDetections();
        const rawLabels = detections
            .map(row => extractFrameLabel(row)[1])
            .filter(Boolean)
            .join('');
        const compacted = compactDetectionRanges(detections);
        const corrected = generateCorrectedLog(detections);
        return { rawLabels, compacted, corrected };
    };

    const getCompactedLog = () => {
        const detections = loadDetections();
        return compactDetectionRanges(detections);
    };

    const getCorrectedLog = () => {
        const detections = loadDetections();
        return generateCorrectedLog(detections);
    };

    window.DetectionUtils = {
        loadDetections,
        saveDetections,
        clearDetections,
        compactDetectionRanges,
        generateCorrectedLog,
        getLogs,
        getCompactedLog,
        getCorrectedLog
    };
})();
