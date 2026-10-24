import { animate, createTimeline, stagger } from 'animejs';

/**
 * Checks whether user prefers reduced motion for accessibility.
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Cleanly cancels an Anime.js animation or timeline instance if active.
 */
export const safeCancel = (instance: any) => {
  if (instance && typeof instance.pause === 'function') {
    instance.pause();
  }
};

/**
 * Standard fade in with subtle upward translation.
 */
export const fadeInUp = (
  targets: any,
  options: { delay?: number; duration?: number; distance?: number; onComplete?: () => void } = {}
) => {
  if (prefersReducedMotion() || !targets) return null;
  const { delay = 0, duration = 600, distance = 16, onComplete } = options;

  const params: Record<string, any> = {
    opacity: [0, 1],
    translateY: [distance, 0],
    duration,
    delay,
    ease: 'outCubic',
  };

  if (onComplete) {
    params.onComplete = onComplete;
  }

  return animate(targets, params as any);
};

/**
 * Staggered entrance for lists of cards or timeline nodes.
 */
export const staggerEntrance = (
  targets: any,
  options: { staggerMs?: number; duration?: number; distance?: number } = {}
) => {
  if (prefersReducedMotion() || !targets) return null;
  const { staggerMs = 70, duration = 550, distance = 14 } = options;

  return animate(targets, {
    opacity: [0, 1],
    translateY: [distance, 0],
    duration,
    delay: stagger(staggerMs),
    ease: 'outCubic',
  } as any);
};

/**
 * Animated numerical counter transitioning from start to end value.
 */
export const animateCounter = (
  element: HTMLElement | null,
  from: number,
  to: number,
  options: { decimals?: number; suffix?: string; duration?: number } = {}
) => {
  if (!element) return;
  const { decimals = 4, suffix = '', duration = 800 } = options;

  if (prefersReducedMotion()) {
    element.textContent = `${to.toFixed(decimals)}${suffix}`;
    return;
  }

  const obj = { val: from };
  return animate(obj, {
    val: to,
    duration,
    ease: 'outExpo',
    onUpdate: () => {
      element.textContent = `${obj.val.toFixed(decimals)}${suffix}`;
    },
    onComplete: () => {
      element.textContent = `${to.toFixed(decimals)}${suffix}`;
    },
  } as any);
};

/**
 * Smooth probability bar width expansion/transition.
 */
export const animateProbabilityBar = (
  target: HTMLElement | null,
  targetWidthPercent: number,
  duration = 600
) => {
  if (!target) return;
  const clamped = Math.max(0, Math.min(100, targetWidthPercent));

  if (prefersReducedMotion()) {
    target.style.width = `${clamped}%`;
    return;
  }

  return animate(target, {
    width: `${clamped}%`,
    duration,
    ease: 'outCubic',
  } as any);
};

/**
 * Scientific Diagram Animation:
 * Animates the 3 competing hypotheses (H1, H2, H3) connecting through candidate assays
 * and converging upon the decisive recommended experiment node (EXP-WGS-02).
 */
export const setupHeroExperimentDiagramAnimation = (elements: {
  hypothesisNodes: (SVGCircleElement | SVGElement)[] | null;
  connectorPaths: SVGPathElement[] | null;
  recommendedNode: SVGCircleElement | SVGElement | null;
  pulseRings: SVGCircleElement[] | null;
  badgeTag: SVGElement | null;
}) => {
  if (prefersReducedMotion()) return null;
  const { hypothesisNodes, connectorPaths, recommendedNode, pulseRings, badgeTag } = elements;

  const tl = createTimeline({
    playbackEase: 'outCubic',
  } as any);

  // 1. Reveal hypothesis nodes
  if (hypothesisNodes && hypothesisNodes.length) {
    tl.add(
      hypothesisNodes,
      {
        opacity: [0, 1],
        scale: [0.6, 1],
        duration: 600,
        delay: stagger(100),
        ease: 'outBack',
      } as any,
      0
    );
  }

  // 2. Animate connector paths dashoffset
  if (connectorPaths && connectorPaths.length) {
    connectorPaths.forEach((path) => {
      const len = path.getTotalLength?.() || 240;
      path.style.strokeDasharray = `${len}`;
      path.style.strokeDashoffset = `${len}`;
    });

    tl.add(
      connectorPaths,
      {
        strokeDashoffset: [240, 0],
        duration: 900,
        delay: stagger(120),
        ease: 'outCubic',
      } as any,
      300
    );
  }

  // 3. Highlight recommended experiment node
  if (recommendedNode) {
    tl.add(
      recommendedNode,
      {
        opacity: [0, 1],
        scale: [0.4, 1.15, 1],
        duration: 700,
        ease: 'outBack',
      } as any,
      850
    );
  }

  // 4. Subtle pulse ring expansion
  if (pulseRings && pulseRings.length) {
    tl.add(
      pulseRings,
      {
        r: [12, 28],
        opacity: [0.7, 0],
        duration: 1100,
        delay: stagger(220),
        ease: 'outQuad',
      } as any,
      1050
    );
  }

  // 5. Reveal EIG callout badge
  if (badgeTag) {
    tl.add(
      badgeTag,
      {
        opacity: [0, 1],
        translateY: [6, 0],
        duration: 500,
        ease: 'outCubic',
      } as any,
      1200
    );
  }

  return tl;
};

/**
 * Viewport-aware scroll reveal helper using IntersectionObserver
 */
export const observeSectionReveal = (
  element: HTMLElement | null,
  onReveal: () => void,
  threshold = 0.15
): (() => void) => {
  if (!element || typeof IntersectionObserver === 'undefined') {
    onReveal();
    return () => {};
  }

  let hasRevealed = false;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !hasRevealed) {
          hasRevealed = true;
          onReveal();
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold }
  );

  observer.observe(element);
  return () => observer.disconnect();
};
