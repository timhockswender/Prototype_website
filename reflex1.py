import reflex as rx
import os
import sqlite3

class ImageData(rx.Base):
    src: str
    alt: str
    name: str
    price: float
    description: str

class State(rx.State):
    active_topic: str = ""
    active_subtopic: str = ""
    active_gallery: str = ""
    is_detail_open: bool = False
    current_image_detail: ImageData = ImageData(src="", alt="", name="", price=0.0, description="")
    cart_items: list[ImageData] = []
    is_cart_open: bool = False

    # Gallery images
    pergamano_images: list[ImageData] = []
    original_images: list[ImageData] = []

    DB_FILE = "artshop.db"

    def toggle_topic(self, topic_name: str):
        if self.active_topic == topic_name:
            self.active_topic = ""
            self.active_subtopic = ""
            self.active_gallery = ""
        else:
            self.active_topic = topic_name
            self.active_subtopic = ""
            self.active_gallery = ""

    def toggle_subtopic(self, subtopic_name: str):
        if self.active_subtopic == subtopic_name:
            self.active_subtopic = ""
            self.active_gallery = ""
        else:
            self.active_subtopic = subtopic_name
            self.active_gallery = ""

    def toggle_gallery(self, gallery_name: str):
        if self.active_gallery == gallery_name:
            self.active_gallery = ""
        else:
            self.active_gallery = gallery_name

    def show_image_detail(self, image: ImageData):
        self.current_image_detail = image
        self.is_detail_open = True

    def close_image_detail(self):
        self.is_detail_open = False

    def add_to_cart(self):
        self.cart_items.append(self.current_image_detail)
        self.close_image_detail()
        self.is_cart_open = True

    def open_cart(self):
        self.is_cart_open = True

    def close_cart(self):
        self.is_cart_open = False

    def clear_cart(self):
        self.cart_items.clear()

    def remove_from_cart(self, index: int):
        if 0 <= index < len(self.cart_items):
            del self.cart_items[index]

    def checkout(self):
        print(f"Checkout for {self.cart_count} items.")
        self.close_cart()
        self.clear_cart()

    @rx.var
    def cart_count(self) -> int:
        return len(self.cart_items)

    @rx.var
    def cart_total(self) -> float:
        return sum(item.price for item in self.cart_items)

    def load_gallery_metadata(self):
        meta = {}
        if not os.path.exists(self.DB_FILE):
            return meta
        try:
            with sqlite3.connect(self.DB_FILE) as conn:
                cur = conn.cursor()
                cur.execute("SELECT image_path, name, price, description FROM gallery_items WHERE display=1")
                for image_path, name, price, description in cur.fetchall():
                    if not image_path:
                        continue
                    fname = os.path.basename(image_path).lower()
                    meta[fname] = {
                        "name": name,
                        "price": price,
                        "description": description
                    }
        except Exception as e:
            print(f"DB loading error: {e}")
            pass
        return meta

    def build_image_list(self, subfolder, meta):
        base = os.path.join("assets", "static", subfolder)
        exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        imgs = []
        if os.path.isdir(base):
            for fn in sorted(os.listdir(base)):
                ext = os.path.splitext(fn)[1].lower()
                if ext in exts:
                    key = fn.lower()
                    m = meta.get(key, {})
                    rel_path = f"/static/{subfolder}/{fn}"
                    alt = m.get("name") or os.path.splitext(fn)[0].replace("_", " ").title()
                    imgs.append(ImageData(
                        src=rel_path,
                        alt=alt,
                        name=m.get("name") or alt,
                        price=m.get("price", 1.50),
                        description=m.get("description", "description")
                    ))
        return imgs

    def load_gallery_metadata_images(self):
        meta = self.load_gallery_metadata()
        self.pergamano_images = self.build_image_list("pergamano", meta)
        self.original_images = self.build_image_list("original", meta)


def topic_card(topic_name, topic_data):
    return rx.box(
        rx.heading(topic_name, size="4", color="black"),
        rx.cond(
            State.active_topic == topic_name,
            rx.box(
                rx.foreach(topic_data.get('subtopics', []), render_subtopic)
            ),
            None
        ),
        on_click=lambda: State.toggle_topic(topic_name),
        style={
            "border_left": f"5px solid {topic_data['color']}",
            "background": "white",
            "border_radius": "15px",
            "padding": "25px",
            "box_shadow": "0 8px 25px rgba(0,0,0,.15)",
            "cursor": "pointer",
            "transition": "all .3s ease",
            "_hover": {
                "transform": "translateY(-6px)",
                "box_shadow": "0 15px 30px rgba(0,0,0,.25)",
            }
        }
    )

def render_subtopic(sub):
    if isinstance(sub, str):
        return rx.box(sub, style={"padding": "8px 12px", "margin": "6px 0"})
    
    if sub.get('type') == 'gallery':
        gallery_name = sub['name']
        images_var = sub.get('images', [])
        return rx.box(
            rx.box(gallery_name, on_click=lambda: State.toggle_gallery(gallery_name), style={
                "padding": "8px 12px", "margin": "6px 0", "cursor": "pointer"
            }),
            rx.cond(State.active_gallery == gallery_name,
                    rx.flex(
                        rx.foreach(images_var, gallery_item),
                        gap="14px", wrap="wrap", margin_top="10px"
                    ),
                    None
            )
        )
    
    if sub.get('subtopics'):
        subtopic_name = sub['name']
        return rx.box(
            rx.box(subtopic_name, on_click=lambda: State.toggle_subtopic(subtopic_name), style={
                "padding": "8px 12px", "margin": "6px 0", "cursor": "pointer"
            }),
            rx.cond(State.active_subtopic == subtopic_name,
                    rx.box(
                        rx.foreach(sub['subtopics'], render_subtopic),
                        padding_left="20px"
                    ),
                    None
            )
        )

    if sub.get('play_sound'):
        return rx.box(sub['name'], style={
            "padding": "8px 12px", "margin": "6px 0"
        })

    return rx.box(sub.get('name', 'Item'), style={"padding": "8px 12px", "margin": "6px 0"})

def gallery_item(img: ImageData):
    return rx.box(
        rx.image(src=img.src, alt=img.alt, width="100%", height="110px", object_fit="cover", border_radius="6px"),
        rx.box(
            rx.box(img.name, font_weight="bold"),
            rx.box(f"${img.price:.2f}", color="#0a7a27", font_weight="bold"),
            rx.box(img.description, font_style="italic", color="#555"),
            margin_top="4px", font_size="0.8rem"
        ),
        on_click=lambda: State.show_image_detail(img),
        width="160px",
        background="#ffffffd9",
        border="1px solid #ddd",
        border_radius="10px",
        padding="6px",
        box_shadow="0 2px 5px rgba(0,0,0,.12)",
        cursor="pointer",
        transition="all .2s ease",
        _hover={
            "box_shadow": "0 4px 10px rgba(0,0,0,.25)",
            "transform": "translateY(-3px)",
        }
    )

def image_detail_overlay():
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header(State.current_image_detail.name),
                rx.modal_body(
                    rx.flex(
                        rx.image(src=State.current_image_detail.src, max_width="430px", max_height="430px", object_fit="cover", border_radius="14px"),
                        rx.box(
                            rx.text(f"${State.current_image_detail.price:.2f}", font_size="1.2rem", font_weight="bold", color="#0a7a27"),
                            rx.text(State.current_image_detail.description, color="#444", white_space="pre-wrap", flex_grow=1),
                            rx.button("Add to Cart", on_click=State.add_to_cart),
                            direction="column",
                            flex=1,
                            gap="1rem"
                        ),
                        gap="1.5rem"
                    )
                ),
                rx.modal_close_button(),
            )
        ),
        is_open=State.is_detail_open,
        on_close=State.close_image_detail
    )

def cart_modal():
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_header("Your Cart"),
                rx.modal_body(
                    rx.cond(
                        State.cart_count > 0,
                        rx.unordered_list(
                            rx.foreach(
                                State.cart_items,
                                lambda item, index: rx.list_item(
                                    rx.text(f"{item.name} - ${item.price:.2f}"),
                                    rx.button("X", on_click=lambda: State.remove_from_cart(index)),
                                    display="flex",
                                    justify_content="space-between",
                                )
                            )
                        ),
                        rx.text("Cart is empty.", font_style="italic", color="#666")
                    )
                ),
                rx.modal_footer(
                    rx.text(f"Total: ${State.cart_total:.2f}", font_weight="bold"),
                    rx.button("Clear Cart", on_click=State.clear_cart),
                    rx.button("Checkout", on_click=State.checkout)
                ),
                rx.modal_close_button(),
            )
        ),
        is_open=State.is_cart_open,
        on_close=State.close_cart
    )

def index():
    TOPICS = {
        'Arts': {
            'subtopics': [
                {'name': 'Pergamano', 'subtopics': [{'name': 'Gallery', 'type': 'gallery', 'images': State.pergamano_images}]},
                {'name': 'Original', 'type': 'gallery', 'images': State.original_images}
            ],
            'color': '#FF6B6B'
        },
        'Soapy Stuff': {
            'subtopics': [{'name': 'Young & Restless', 'play_sound': 'Nadia1.wav'}, 'General Hospital'],
            'color': '#4ECDC4'
        },
        'Python': {
            'subtopics': ['Articles', 'A. I. Related', 'Finance', 'Science'],
            'color': '#45B7D1'
        },
        'News': {
            'subtopics': ['NYT Daily Update', 'Subscribe'],
            'color': '#96CEB4'
        },
        'Chemistry': {
            'subtopics': ['Polymers', 'Simulation', 'Discoveries'],
            'color': '#FFEAA7'
        }
    }
    
    return rx.container(
        rx.flex(
            rx.button("See Cart", on_click=State.open_cart),
            justify="end",
            margin_bottom="10px"
        ),
        rx.heading("My Topics Explorer", size="3", text_align="center", color="white", margin="10px 0 15px"),
        rx.text("Click a topic to expand. Click a gallery name, then click an image for details.", text_align="center", color="rgba(255,255,255,.85)", margin_top="5px"),
        rx.grid(
            rx.foreach(
                list(TOPICS.items()),
                lambda item: topic_card(item[0], item[1])
            ),
            grid_template_columns="repeat(auto-fit, minmax(220px, 1fr))",
            gap="20px",
        ),
        image_detail_overlay(),
        cart_modal(),
        on_load=State.load_gallery_metadata_images,
        max_width="1250px",
        margin="0 auto",
        style={
            "body": {
                "font_family": "Segoe UI, Arial, sans-serif",
                "background": "linear-gradient(135deg,#667eea 0%,#764ba2 100%)",
                "padding": "20px",
                "min_height": "100vh",
                "margin": "0"
            }
        }
    )

app = rx.App()
app.add_page(index, title = "Family_web_Site")