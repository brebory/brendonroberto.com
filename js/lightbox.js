/* Click any image in a figure to see it larger, with its caption.
   Shared by every page; styles are injected here so the homepage and
   the posts don't each need a copy. Pixel art stays unsmoothed and keeps
   its aspect ratio, scaled up by a whole number where it fits. Images that
   aren't inside a link get keyboard support so everyone can open them. */
(function () {
	var images = document.querySelectorAll("figure img");
	if (!images.length || !window.HTMLDialogElement) return;

	var style = document.createElement("style");
	style.textContent =
		".lightbox { max-width: 96vw; max-height: 96vh; padding: 0; border: none; background: transparent; overflow: hidden; }" +
		".lightbox::backdrop { background: rgba(10, 14, 22, 0.88); }" +
		".lightbox img { display: block; max-width: 94vw; max-height: 86vh; margin: 0 auto; border-radius: 6px; cursor: zoom-out; }" +
		".lightbox img.pixel { max-width: none; max-height: none; image-rendering: pixelated; }" +
		".lightbox p { margin: 0.5em 0 0; color: #ffffff; font-family: \"Gentium Book Basic\", Georgia, serif; font-style: italic; text-align: center; }" +
		"figure img.zoomable { cursor: zoom-in; }" +
		"figure img.zoomable:focus-visible { outline: 3px solid #1E81FA; outline-offset: 3px; }";
	document.head.appendChild(style);

	var box = document.createElement("dialog");
	box.className = "lightbox";
	box.setAttribute("aria-label", "Enlarged image");
	var big = document.createElement("img");
	var caption = document.createElement("p");
	box.appendChild(big);
	box.appendChild(caption);
	document.body.appendChild(box);
	box.addEventListener("click", function () { box.close(); });

	// Pixel art: fit inside 94vw x 86vh without changing its shape, using a
	// whole-number scale when it's being enlarged so every pixel stays square.
	function sizePixelArt() {
		if (!big.classList.contains("pixel") || !big.naturalWidth) return;
		var fit = Math.min(
			window.innerWidth * 0.94 / big.naturalWidth,
			window.innerHeight * 0.86 / big.naturalHeight
		);
		var scale = fit >= 1 ? Math.floor(fit) : fit;
		big.style.width = Math.round(big.naturalWidth * scale) + "px";
		big.style.height = Math.round(big.naturalHeight * scale) + "px";
	}
	big.addEventListener("load", sizePixelArt);
	window.addEventListener("resize", function () { if (box.open) sizePixelArt(); });

	function open(img, link) {
		var figure = img.closest("figure");
		var figcaption = figure && figure.querySelector("figcaption");
		var href = link && link.getAttribute("href");
		// Drop the previous image first so it never shows under the new caption.
		big.removeAttribute("src");
		big.style.width = "";
		big.style.height = "";
		big.className = img.classList.contains("pixel") ? "pixel" : "";
		big.alt = img.alt;
		big.src = href && /\.(webp|png|jpe?g|gif)$/i.test(href) ? href : img.currentSrc || img.src;
		caption.textContent = figcaption ? figcaption.textContent : "";
		caption.hidden = !figcaption;
		box.showModal();
		if (big.complete) sizePixelArt();
	}

	images.forEach(function (img) {
		var link = img.closest("a");
		img.classList.add("zoomable");
		if (link) {
			link.addEventListener("click", function (e) {
				e.preventDefault();
				open(img, link);
			});
			return;
		}
		// Not inside a link: make the image itself focusable and keyboard-operable.
		img.tabIndex = 0;
		img.setAttribute("role", "button");
		img.setAttribute("aria-label", "Enlarge image" + (img.alt ? ": " + img.alt : ""));
		img.addEventListener("click", function () { open(img, null); });
		img.addEventListener("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				open(img, null);
			}
		});
	});
})();
