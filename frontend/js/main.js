
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.getElementById("navbar");
  const menuToggle = document.getElementById("menuToggle");
  const navLinks = document.getElementById("navLinks");
  const heroVideo = document.getElementById("heroVideo");
  const demoButton = document.getElementById("demoButton");
  const demoLabel = document.getElementById("demoLabel");
  const playIcon = document.getElementById("playIcon");
  const currentYear = document.getElementById("currentYear");

  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  // Footer year
  if (currentYear) {
    currentYear.textContent = new Date().getFullYear();
  }

  // Navbar appearance on scroll
  function updateNavbar() {
    if (!navbar) return;
    navbar.classList.toggle("scrolled", window.scrollY > 35);
  }

  updateNavbar();
  window.addEventListener("scroll", updateNavbar, { passive: true });

  // Mobile navigation
  if (menuToggle && navLinks) {
    menuToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("open");

      menuToggle.setAttribute("aria-expanded", String(isOpen));
      menuToggle.setAttribute(
        "aria-label",
        isOpen ? "Close navigation" : "Open navigation"
      );
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
        menuToggle.setAttribute("aria-label", "Open navigation");
      });
    });

    document.addEventListener("click", (event) => {
      if (
        !navLinks.contains(event.target) &&
        !menuToggle.contains(event.target)
      ) {
        navLinks.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
        menuToggle.setAttribute("aria-label", "Open navigation");
      }
    });
  }

  // Hero video playback
  function updateDemoButton() {
    if (!heroVideo || !demoButton || !demoLabel || !playIcon) return;

    const isPaused = heroVideo.paused;

    demoLabel.textContent = isPaused
      ? "Play Background"
      : "Pause Background";

    playIcon.innerHTML = isPaused
      ? `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
           <path d="m9 6 9 6-9 6V6Z"
             stroke="currentColor" stroke-width="1.7"
             stroke-linejoin="round"/>
         </svg>`
      : `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
           <path d="M8 6v12M16 6v12"
             stroke="currentColor" stroke-width="2"
             stroke-linecap="round"/>
         </svg>`;

    demoButton.setAttribute(
      "aria-label",
      isPaused ? "Play background video" : "Pause background video"
    );
  }

  if (heroVideo && demoButton) {
    // Reduced-motion users get a still poster until they choose to play.
    if (reducedMotion) {
      heroVideo.pause();
    }

    demoButton.addEventListener("click", async () => {
      if (heroVideo.paused) {
        try {
          await heroVideo.play();
        } catch (error) {
          console.warn("The hero video could not be played.", error);
        }
      } else {
        heroVideo.pause();
      }

      updateDemoButton();
    });

    heroVideo.addEventListener("play", updateDemoButton);
    heroVideo.addEventListener("pause", updateDemoButton);
    heroVideo.addEventListener("ended", updateDemoButton);

    // Keep the page usable if the video file is missing or unsupported.
    heroVideo.addEventListener("error", () => {
      console.warn(
        "TrackBus hero video could not be loaded. Check assets/trackbus-hero.mp4."
      );
      updateDemoButton();
    });

    updateDemoButton();
  }

  // Scroll reveal animation
  const revealElements = document.querySelectorAll(".reveal");

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealElements.forEach((element) => {
      element.classList.add("visible");
    });
  } else {
    const observer = new IntersectionObserver(
      (entries, currentObserver) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            currentObserver.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.12,
        rootMargin: "0px 0px -35px 0px"
      }
    );

    revealElements.forEach((element) => {
      observer.observe(element);
    });
  }

  // Highlight the current navigation section
  const sectionLinks = document.querySelectorAll(
    '.nav-links a[href^="#"]'
  );

  const sections = Array.from(sectionLinks)
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;

          sectionLinks.forEach((link) => {
            link.classList.toggle(
              "active",
              link.getAttribute("href") === `#${entry.target.id}`
            );
          });
        });
      },
      {
        rootMargin: "-30% 0px -60% 0px"
      }
    );

    sections.forEach((section) => sectionObserver.observe(section));
  }
});


