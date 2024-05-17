from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404

from marketplace.context_processors import get_cart_counter, get_cart_amounts
from marketplace.models import Cart
from menu.models import Category, FoodItem
from vendor.models import Vendor, OpeningHour


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)


def vendor_detail(request, vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset=FoodItem.objects.filter(is_available=True),
        )
    )
    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', '-from_hour')

    # Check current day's opening hours.
    today_date = date.today()
    today = today_date.isoweekday()

    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    checkcart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase the cart quantity
                    checkcart.quantity += 1
                    checkcart.save()
                    return JsonResponse({'status': "Success", 'message': 'Increased the cart quantity!', 'cart_counter': get_cart_counter(request), 'qty': checkcart.quantity, 'cart_amounts': get_cart_amounts(request)})
                except:
                    checkcart = Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)
                    return JsonResponse({'status': "Success", 'message': 'Added the food to the cart!', 'cart_counter': get_cart_counter(request), 'qty': checkcart.quantity, 'cart_amounts': get_cart_amounts(request)})

            except:
                return JsonResponse({'status': "Failed", 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': "Failed", 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': "login_required", 'message': 'please login to continue'})


def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    checkcart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if checkcart.quantity > 1:
                        # decrease the cart quantity
                        checkcart.quantity -= 1
                        checkcart.save()
                    else:
                        checkcart.delete()
                        checkcart.quantity = 0
                    return JsonResponse({
                        'status': "Success", 'cart_counter': get_cart_counter(request), 'qty': checkcart.quantity,
                        'cart_amounts': get_cart_amounts(request)
                    })
                except:
                    return JsonResponse({
                        'status': "Failed", 'message': 'You do not have this item in your cart!',
                        'counter': get_cart_counter(request)
                    })

            except:
                return JsonResponse({'status': "Failed", 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': "Failed", 'message': 'Invalid request!'})
    else:
        return JsonResponse({'status': "login_required", 'message': 'please login to continue'})


@login_required(login_url='login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items': cart_items
    }
    return render(request, 'marketplace/cart.html', context)


def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # check if the cart item exist
                cart_item = Cart.objects.filter(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({
                        'status': "Success", 'message': 'Cart item has been deleted!',
                        'cart_counter': get_cart_counter(request), 'cart_amounts': get_cart_amounts(request)
                    })
            except:
                return JsonResponse({'status': "Failed", 'message': 'Cart item does not exist!'})
    else:
        return JsonResponse({'status': "login_required", 'message': 'please login to continue'})


def search(request):
    location = request.GET['location']
    radius = request.GET['radius']
    keyword = request.GET['keyword']
    fetch_vendors_by_fooditem = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True)\
        .values_list('vendor', flat=True)
    vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_fooditem) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True))

    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)
