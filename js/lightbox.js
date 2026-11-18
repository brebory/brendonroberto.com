/* Click any image in a figure to see it larger, with its caption.
   Shared by every page; styles are injected here so the homepage and
   the posts don't each need a copy. Pixel art stays unsmoothed. */
(function () {
	var images = document.querySelectorAll("figure img");
	if (!images.length || !window.HTMLDialogElement) return;

	var style = document.createElement("style");
	style.textContent =
		".lightbox { max-width: 96vw; max-height: 96vh; padding: 0; border: none; background: transparent; }" +
		".lightbox::backdrop { background: rgba(10, 14, 22, 0.88); }" +
		".lightbox img { display: block; max-width: 94vw; max-height: 86vh; margin: 0 auto; border-radius: 6px; cursor: zoom-out; }" +
		".lightbox img.pixel { width: min(94vw, 86vh); height: auto; image-rendering: pixelated; }" +
		".lightbox p { margin: 0.5em 0 0; color: #ffffff; font-family: \"Gentium Book Basic\", Georgia, serif; font-style: italic; text-align: center; }" +
		"figure img.zoomable { cursor: zoom-in; }";
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

	images.forEach(function (img) {
		var link = img.closest("a");
		img.classList.add("zoomable");
		(link || img).addEventListener("click", function (e) {
			e.preventDefault();
			var figure = img.closest("figure");
			var figcaption = figure && figure.querySelector("figcaption");
			big.src = link && /\.(webp|png|jpe?g|gif)$/i.test(link.getAttribute("href")) ? link.getAttribute("href") : img.currentSrc || img.src;
			big.alt = img.alt;
			big.className = img.classList.contains("pixel") ? "pixel" : "";
			caption.textContent = figcaption ? figcaption.textContent : "";
			caption.hidden = !figcaption;
			box.showModal();
		});
	});
})();
