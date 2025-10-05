from django.urls import path
from.import views

urlpatterns = [
    #user
    path("add-product-image/", views.upload_image, name="addproductimage"),
    path("user-products/", views.user_product_list, name="product_lists"),
    path("product-details/<slug>/", views.product_detail, name="product_detail"),
    path("product-update/<slug>/",views.product_update, name="product_update"),
    path("product-delete/<slug>/",views.product_delete, name="product_delete"),
    path("add-to-cart/<product_id>/", views.add_to_cart, name = "add-to-cart"),
    path("cart/",views.view_cart, name="cart"),
    path("remove-cart-item<product_id>/", views.remove_item, name="remove_item"),
    path("shipping/", views.shipping_view, name ="shipping"),
    path("initiate-payment/", views.initiate_payment, name="initiate_payment"),
    path("verify-payment/", views.verify_payment, name="verify_payment"),
    path("search/", views.search_view, name="search"),
    path("update-cart/<int:product_id>/", views.update_cart_quantity, name="update_cart"),
    path("cart/increase/<int:item_id>/", views.increase_quantity, name="increase_quantity"),
    path("cart/decrease/<int:item_id>/", views.decrease_quantity, name="decrease_quantity"),
    path("products/", views.product_list, name="product_list"),
    path("categories/<int:category_id>/", views.category_products, name="category_products"),
    path("Seller-dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("Buyer-dashboard/", views.buyer_dashboard, name="buyer_dashboard"),
    path("sell-analytics/",views.seller_analytics, name="sell-analytics"),
]