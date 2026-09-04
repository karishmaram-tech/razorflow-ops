import { useMemo } from 'react';
import { motion } from 'framer-motion';

function getStaggerChildren(text, staggerFrom, staggerDuration) {
  const chars = text.split('');
  const total = chars.length;

  return chars.map((char, i) => {
    const index = staggerFrom === 'first' ? i : total - 1 - i;
    return {
      char,
      delay: index * staggerDuration,
    };
  });
}

function FlipChar({ char, delay, rotateDirection, transition, className }) {
  if (char === ' ') {
    return <span className="inline-block">&nbsp;</span>;
  }

  const initialRotation = rotateDirection === 'top' ? -90 : 90;
  const originY = rotateDirection === 'top' ? 0 : 1;

  return (
    <motion.span
      className={`inline-block ${className || ''}`}
      initial={{ rotateX: initialRotation, opacity: 0 }}
      animate={{ rotateX: 0, opacity: 1 }}
      transition={{
        ...transition,
        delay,
      }}
      style={{ perspective: '400px', transformOrigin: `center ${originY === 0 ? 'top' : 'bottom'} 0px` }}
    >
      {char}
    </motion.span>
  );
}

export default function Text3DFlip({
  children,
  className,
  textClassName,
  flipTextClassName,
  rotateDirection = 'top',
  staggerDuration = 0.03,
  staggerFrom = 'first',
  transition = { type: 'spring', damping: 25, stiffness: 160 },
}) {
  const text = typeof children === 'string' ? children : '';
  const words = text.split(' ');

  const staggeredChars = useMemo(
    () => getStaggerChildren(text, staggerFrom, staggerDuration),
    [text, staggerFrom, staggerDuration]
  );

  let charIndex = 0;    return (
    <div className={`overflow-hidden ${className || ''}`}>
      {words.map((word, wordIdx) => (
        <span key={wordIdx} className="inline-block mr-[0.25em]">
          {word.split('').map((char, i) => {
            const { delay } = staggeredChars[charIndex];
            charIndex++;
            return (
              <FlipChar
                key={`${wordIdx}-${i}`}
                char={char}
                delay={delay}
                rotateDirection={rotateDirection}
                transition={transition}
                className={flipTextClassName || textClassName}
              />
            );
          })}
        </span>
      ))}
    </div>
  );
}
