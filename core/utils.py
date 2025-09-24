from decimal import Decimal
from django.conf import settings
from .models import Product
import openai
from django.utils.translation import get_language


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price) if product.price else '0'
            }
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session['cart'] = self.cart
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            if 'product' in item:
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
            if item['price'] != '0'
        )

    def clear(self):
        del self.session['cart']
        self.session.modified = True

    def get_items(self):
        items = []
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            cart_item = self.cart[str(product.id)]
            items.append({
                'product': product,
                'quantity': cart_item['quantity'],
                'price': Decimal(cart_item['price']) if cart_item['price'] != '0' else None,
                'total_price': (
                    Decimal(cart_item['price']) * cart_item['quantity']
                    if cart_item['price'] != '0' else None
                )
            })
        return items


class AIProductEnricher:
    """Utility class for AI-powered product data enrichment"""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def generate_description(self, product, language='it'):
        """Generate an AI-powered product description"""
        if not settings.OPENAI_API_KEY:
            return None

        try:
            prompt = self._build_prompt(product, language)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(language)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error generating AI description: {e}")
            return None

    def _get_system_prompt(self, language):
        if language == 'en':
            return (
                "You are a professional copywriter for an industrial products company. "
                "Write clear, technical, and informative product descriptions that highlight "
                "key features, applications, and benefits for B2B customers."
            )
        else:  # Italian
            return (
                "Sei un copywriter professionista per un'azienda di prodotti industriali. "
                "Scrivi descrizioni di prodotti chiare, tecniche e informative che evidenzino "
                "caratteristiche principali, applicazioni e benefici per clienti B2B."
            )

    def _build_prompt(self, product, language):
        if language == 'en':
            prompt = f"""
            Create a professional product description for:
            Product: {product.name}
            Brand: {product.brand.name if product.brand else 'N/A'}
            Category: {product.category.name if product.category else 'N/A'}
            Current Description: {product.description or 'Not available'}
            Application: {product.application or 'Not specified'}

            Write a compelling 2-3 paragraph description focusing on technical specifications,
            key benefits, and typical applications. Use professional industrial terminology.
            """
        else:  # Italian
            prompt = f"""
            Crea una descrizione professionale del prodotto per:
            Prodotto: {product.name}
            Marca: {product.brand.name if product.brand else 'N/D'}
            Categoria: {product.category.name if product.category else 'N/D'}
            Descrizione attuale: {product.description or 'Non disponibile'}
            Applicazione: {product.application or 'Non specificata'}

            Scrivi una descrizione convincente di 2-3 paragrafi concentrandoti su specifiche tecniche,
            benefici principali e applicazioni tipiche. Usa terminologia industriale professionale.
            """
        return prompt

    def translate_content(self, text, target_language):
        """Translate product content to target language"""
        if not settings.OPENAI_API_KEY or not text:
            return text

        try:
            source_lang = 'Italian' if target_language == 'en' else 'English'
            target_lang = 'English' if target_language == 'en' else 'Italian'

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in industrial and technical content. "
                                   f"Translate from {source_lang} to {target_lang} maintaining technical accuracy."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this industrial product text to {target_lang}: {text}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )

            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error translating content: {e}")
            return text

    def generate_seo_metadata(self, product, language='it'):
        """Generate SEO-optimized title and description"""
        if not settings.OPENAI_API_KEY:
            return None, None

        try:
            if language == 'en':
                prompt = f"""
                Generate SEO metadata for this industrial product:
                Product: {product.name}
                Brand: {product.brand.name if product.brand else ''}
                Category: {product.category.name if product.category else ''}

                Provide:
                1. Meta Title (max 60 characters)
                2. Meta Description (max 160 characters)

                Format: Title: [title]\nDescription: [description]
                """
            else:
                prompt = f"""
                Genera metadata SEO per questo prodotto industriale:
                Prodotto: {product.name}
                Marca: {product.brand.name if product.brand else ''}
                Categoria: {product.category.name if product.category else ''}

                Fornisci:
                1. Meta Title (max 60 caratteri)
                2. Meta Description (max 160 caratteri)

                Formato: Title: [titolo]\nDescription: [descrizione]
                """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO expert for industrial products."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )

            result = response.choices[0].message['content'].strip()
            lines = result.split('\n')
            title = lines[0].replace('Title:', '').strip() if lines else None
            description = lines[1].replace('Description:', '').strip() if len(lines) > 1 else None

            return title, description
        except Exception as e:
            print(f"Error generating SEO metadata: {e}")
            return None, None