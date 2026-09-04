import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export function AnimatedList({ children, className = '', delay = 1500 }) {
  const [items, setItems] = useState([]);
  const childArray = Array.isArray(children) ? children : [children];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (index < childArray.length) {
      const timer = setTimeout(() => {
        setItems(prev => [...prev, childArray[index]]);
        setIndex(prev => prev + 1);
      }, index === 0 ? 0 : delay);
      return () => clearTimeout(timer);
    }
  }, [index, childArray.length, delay]);

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <AnimatePresence>
        {items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              type: 'spring',
              damping: 20,
              stiffness: 200,
              delay: 0,
            }}
          >
            {item}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
