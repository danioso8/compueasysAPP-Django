from email.mime import image
from django.shortcuts import render, redirect
from contable.models import ProductContsble as Product

# Create your views here.
def product(request):    
    products = Product.objects.all()
    total_stock = sum(product.stock for product in products)
    for p in products:
        p.final_price = p.price - p.descuento
    return render(request, 'product.html', {'products': products, 'total_stock': total_stock})

def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price', 0))
        stock = int(request.POST.get('stock', 0))
        categoria = request.POST.get('categoria')
        iva = float(request.POST.get('iva', 0.00))
        descuento = float(request.POST.get('descuento', 0.00))
        imagen = request.FILES.get('images')
        galeria = request.FILES.getlist('galeria')  

        # Crea el producto principal
        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            descuento=descuento,
            categoria=categoria,
            iva=iva,
            imagen=imagen
        )

        # Crea las imágenes de galería y las asocia al producto
        for img in galeria:
            galeria_obj = Galeria.objects.create(image=img)
            product.galeria.add(galeria_obj)

        return redirect('product')
    return redirect('product')

def product_edit(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.save()
        return redirect('product')
    return render(request, 'product_edit.html', {'product': product})

def product_delete(request, product_id):
    product = Product.objects.get(id=product_id)
    product.delete()
    return redirect('product')

