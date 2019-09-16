import bpy
from . nVector import nVector
from mathutils import Vector
import math
import os



bl_info = {
    "name": "nCNC",
    "description": "CNC Kontrolü",
    "author": "Nesivmi (nesivmi@gmail.com)",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "View3D",
    "warning": "This addon is still in development.Bu eklenti gelişim aşamasındadır.",
    "wiki_url": "",
    "category": "Generic"}



################
# GRBL G KODLARI
################
# Link  : http://domoticx.com/mechanica-firmware-grbl-arduino-cnc-shield/
# G0, G1: Doğrusal hareket          --> Hızlı / Talaşlı
# G2, G3: Daire, çembersel hareket  --> Saat  / Tersi yön
# G4    : Bekletme komutu           --> G4 P3   3sn bekle
# G10 L2, G10 L20   : Çalışma sıfırı--> G54 - G59 yerine, GRBL bu kodları kullanıyor
# G17, G18, G19     : Düzlem seçimi --> XY / XZ / YZ
# G20, G21          : Units         --> inch / mm
# G28, G30          : Referans nokta--> Tezgah Sıfırına gönder / Önceki noktaya dön
# G28.1, G30.1      : Referans nokta--> Noktayı değiştir
# G38.2             : Probing
# G40               : Takım (kesici) uç yarıçap telafisi iptali
# G43.1, G49        : Dynamic Tool Length Offsets
# G53               : Tezgahın kendi koordinat sistemini seçer
# G54, G55, G56, G57, G58, G59: Çalışma koordinat sistemi
# G61               : Path Control Modes
# G80               : Motion Mode Cancel
# G90, G91          : Mesafe modu       --> Mutlak / Eklemeli
# G91.1             : Arc IJK Distance Modes
# G92               : Coordinate Offset
# G92.1             : Clear Coordinate System Offsets
# G93, G94          : Feedrate Modes

# M0, M2, M30   : Programı durdur / Program sonu / Program sonu ve başa dönüş
# M3, M4, M5    : Motor Döndür      --> Saat yönü / Tersi yön / Durdur
# M7* , M8, M9  : Coolant Control
# M56*          : Parking Motion Override Control

# I, J, K       : Daire merkezi belirtme kodları    --> X / Y / Z yönünde
# F             : Feed  --> İlerleme Hızı mm/dk  Örn F2000  --> G1, G2, G3 ile kullanılır. G0 Kodu ile kullanılmaz
# S             : Speed --> Devir sayısı dev/dk  Örn S500   --> M3 ve M4 kodlarıyla kullanılır
# P             : Pause --> Bekleme süresi /ms   Örn P2000  --> 2 sn bekle

# GRBL'de olmayan FANUC kodlar;
# O :   Program numarasını belirtir; 01234; --> 1234 numaralı program

# Diğer bilgiler
# print(locals()) : local değerleri verir






class NCNC_PR_Props(bpy.types.PropertyGroup):

    def malzeme_poll(self, obj=None):
        return obj.type == "MESH"


    malzeme: bpy.props.PointerProperty( name="Malzeme",
                                        type=bpy.types.Object,
                                        description="Object: Mesh türünde olmalı",
                                        poll=malzeme_poll )





class NCNC_PT_Malzeme(bpy.types.Panel):
    bl_idname = "NCNC_PT_materials_panel"
    bl_label = "Malzeme"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    def draw(self, context):

        layout = self.layout
        scn = context.scene     # context.object
        scn_stg = scn.ncnc_props

        row = layout.row()
        row.prop(scn_stg,"malzeme")





########################################################################################
########################################################################################
#####   Araçlar - Tools



class NCNC_OT_Tools(bpy.types.Operator):
    bl_idname = "ncnc.tools_ops"
    bl_label = "Çalışma alanını ayarlayıcı"
    bl_description = "Yok"
    bl_options = {'REGISTER'}

    action : bpy.props.EnumProperty(items=[
        ("mod", "mod", "Modu ayarlar"),
        ("new", "new", "Çalışma alanındakileri siler ve yeniler."),
    ])


    def invoke(self, context, event=None):

        if self.action == "mod":
            self.birimleri_ayarla(context)
            self.report({'INFO'}, "Curve çizim ayarlarını uygula")
        elif self.action == "new":
            self.birimleri_ayarla(context)
            self.calisma_alanini_sifirla(context)
            self.report({'INFO'}, "Çalışma alanını yenile")


        return {"FINISHED"}


    def birimleri_ayarla(self, context):

        unit = context.scene.unit_settings
        view = context.space_data
        if unit.scale_length != 0.001:
            unit.scale_length = 0.001
        if unit.length_unit != 'MILLIMETERS':
            unit.length_unit = 'MILLIMETERS'
        #if view.clip_end != 100000:
        #    view.clip_end = 100000
        bpy.ops.view3d.view_axis(type="TOP")


    def calisma_alanini_sifirla(self, context=None):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
        bpy.ops.curve.primitive_bezier_curve_add(radius=20, enter_editmode=False, location=(0, 0, 0))
        bpy.ops.view3d.view_all(center=True)
        context.active_object.ncnc_objayar.dahil = True




class NCNC_PT_Tools(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Araçlar"
    bl_idname = "NCNC_PT_tools"

    def draw(self, context):

        layout = self.layout
        scn = context.scene

        row = layout.row()
        row.operator("ncnc.tools_ops", text="", icon="FILE_NEW").action = "new"
        row.operator("ncnc.tools_ops", text="", icon="SETTINGS").action = "mod"
        # icon=obj.baglanti.durum_icon)
        # ,translate=False, expand=True, slider=True, toggle=1, icon_only=False, event=True, full_event=False, emboss=True, index=-1, icon_value=0, )





########################################################################################
########################################################################################
#####   Save - Kayıt Etme

class NCNC_PR_Save(bpy.types.PropertyGroup):

    def write_update(self, context=None):
        if self.write == "overwrite":       # Aynı isimde dosya varsa, dosyanın üstüne yazar
            pass
        elif self.write == "yeniwrite":     # Aynı isimde dosya varsa, yeni dosya ismi üretir
            dl = os.listdir(self.dirpath)   # Mevcut konumdaki, dosya isimlerini listeler
            f = self.filename + self.uzanti # Bizim girdiğimizi dosya ismini alır
            toplam = ""
            if f in dl:                         # Dosya ismi, listede var mı, varsa yeni isim
                count = len(self.filename) -1
                for i in range(count, 0, -1):
                    o = self.filename[i]
                    if o.isdigit():
                        toplam = o + toplam
                        self.filename = self.filename[:i]
                sira = int(toplam) + 1 if toplam else 1
                self.filename = self.filename + str(sira)

                f = self.filename + self.uzanti
                if f in dl:                     # Yeni üretilen isim, konumda varsa, yeni üret
                    self.write_update(context)



    write : bpy.props.EnumProperty(items=[  ("overwrite", "O","Overwrite : Dosya varsa üstüne yaz"),
                                            ("yeniwrite", "N", "New : Yeni dosya oluştur") ],
                                   description="Aynı isimde dosya varsa hangisini seçsin. O:Üstüne yazar, N:Yeni oluşturur",
                                   update=write_update)

    dirpath : bpy.props.StringProperty( name='Yol',
                                        default="/home/huy/Masaüstü/",
                                        description='.nc dosyasının kaydedileceği yer',
                                        subtype='DIR_PATH' )

    filename : bpy.props.StringProperty(name='İsim',
                                        default="CNC_taslak",
                                        description='Dosyanın ismi ne olsun' )

    uzanti : bpy.props.EnumProperty(items=[ (".ngc",    ".ngc",     ""),
                                            (".nc",     ".nc",      ""),
                                            (".cnc",    ".cnc",     ""),
                                            (".gcode",  ".gcode",   ""),
                                            ])





class NCNC_OT_Save(bpy.types.Operator):
    bl_idname = "ncnc.save_ops"
    bl_label = "Dışa Aktar"
    bl_description = "Seçilen konuma, seçilen isim ve uzantıyla kayıt eder"
    bl_options = {'REGISTER'}
    kodlar = []
    sekil = 0
    block = 0
    def invoke(self, context, event=None):

        self.kodlar.clear()
        self.add_header()
        self.sekil = 0

        for obj in bpy.data.objects:
            if not obj.ncnc_objayar.dahil:
                continue
            elif obj.type == 'CURVE':
                ayar = obj.ncnc_objayar
                self.dongu = []
                if ayar.derin % ayar.step > 0.01: self.dongu.append( round(ayar.derin % ayar.step, ayar.yvrla_koor) )

                self.dongu.extend([ i * ayar.step for i in range( 1, int( ayar.derin / ayar.step + 1), ) ])

                self.block = 0
                self.sekil += 1

                self.add_block(expand="1", enable="1")
                self.kodlar.append("{} ( Duzlem )".format(obj.ncnc_objayar.duzlm))
                self.kodlar.append("S{} ( Spindle Hizi )".format(obj.ncnc_objayar.hiz_s))
                self.kodlar.append("( Guvenli yukseklik : {} )".format(obj.ncnc_objayar.gyuk))
                self.kodlar.append("( Son derinlik  (mm) : {} )".format(obj.ncnc_objayar.derin))
                self.kodlar.append("( Adim derinligi (mm) : {} )".format(obj.ncnc_objayar.step))
                self.kodlar.append("( Dalma hizi    (mm/dk) : {} )".format(obj.ncnc_objayar.hiz_d))
                self.kodlar.append("( Ilerleme hizi (mm/dk) : {} )".format(obj.ncnc_objayar.hiz_f))
                self.convert_gcode(obj)


        self.add_footer()
        self.kaydet()
        self.report({"INFO"}, "Kaydedildi > %s" % ( self.file_path ))
        return {"FINISHED"}



    def add_header(self):
        self.add_block(name="Header", expand="1", enable="1")
        self.kodlar.append("(Blender'da nCNC eklentisi tarafindan uretildi )")
        self.kodlar.append("M3 S1200")
        self.kodlar.append("G4 P3")     # 3sn bekle
        self.kodlar.append("G21 (All units in mm)")
        self.kodlar.append("G0 Z5")



    def add_footer(self):
        self.add_block(name="Footer", expand="1", enable="1")
        self.kodlar.append("G0 Z5")
        self.kodlar.append("M5")
        self.kodlar.append("G0 X0 Y0")
        self.kodlar.append("M2")
        self.kodlar.append("(Toplam Satir Sayisi : {})".format(len(self.kodlar)))



    def add_block(self, name=None, expand="0", enable="1"):
        self.kodlar.append("") if len( self.kodlar ) > 0 else None
        self.kodlar.append("(Block-name: " + ("Sekil{}.{})".format(self.sekil, self.block) if not name else name+")"))
        self.kodlar.append("(Block-expand: %s)" % expand)
        self.kodlar.append("(Block-enable: %s)" % enable)



    def convert_gcode(self, obj):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # Scale'ı uygula (1,1,1) yap

        for i, subcurve in enumerate(obj.data.splines):     # Curve altındaki tüm Spline'ları sırayla al
            self.block += 1
            self.add_block(expand="0", enable="1")          # Yeni bir blok başlığı ekle

            curvetype = subcurve.type
            print("curvetype",curvetype)
            for i in self.dongu:
                self.z_adim = Vector((0, 0, i))
                if curvetype == 'NURBS':
                    ### !!! Yapım aşamasında

                    # print("curve is closed:", subcurve.use_cyclic_u)
                    xl = []
                    yl = []
                    #for i in range(11):
                    #    a = nVector.bul_nurbs_1t1pl(0.1 * i, context)
                    #    # print(a)
                    #    xl.append(a.x)
                    #    yl.append(a.y)
                    # empty = bpy.data.objects["Empty"].location
                    # print("a",a)
                    # empty.x = a.x
                    # empty.y = a.y
                    # empty.z = a.z

                    # print("a",a)
                    # for nurbspoint in subcurve.points:
                    #    print([nurbspoint.co[0], nurbspoint.co[1], nurbspoint.co[2]], ',')

                elif curvetype == 'POLY':                       # Poly tipindeki Spline'ı convert et

                    self.poly(obj, subcurve)

                elif curvetype == 'BEZIER':                     # Bezier tipindeki Spline'ı convert et
                    self.bezier(obj, subcurve)



    def bezier(self, obj, subcurve):

        pref = obj.ncnc_objayar
        rc = pref.yvrla_cmbr
        r = pref.yvrla_koor
        z_safe = pref.gyuk

        nokta_sayisi = len(subcurve.bezier_points) - (0 if subcurve.use_cyclic_u else 1)

        nokta_list = []
        for j in range(nokta_sayisi):
            cycle_point = j == nokta_sayisi - 1 and subcurve.use_cyclic_u
            lp = 0 if cycle_point else j + 1                # last point : son nokta

            m1 = subcurve.bezier_points[j].co + obj.location - self.z_adim
            hr = subcurve.bezier_points[j].handle_right + obj.location - self.z_adim
            hl = subcurve.bezier_points[lp].handle_left + obj.location - self.z_adim
            m2 = subcurve.bezier_points[lp].co + obj.location - self.z_adim


            # Aşağıda yapılan iş şöyle özetlenebilir;
            #   Üstteki m1 ve m2 (baş ve son) noktaları arasından alınan 3 değer ile bir inceleme yapılır
            #   Bu m1, m2 ve diğer 3 değerin;
            #       Bir çember üzerinde mi
            #       Bir doğru üzerinde mi
            #                           .. olduğu kontrol edilir. Eğer öyleyseler daha az Gkodu elde edilir

            sorgula = [0.25, 0.5, 0.75]
            bak_merkez = []
            bak_dogru = []
            for i in sorgula:
                ps = nVector.bul_bezier_nokta_4p1t(i, m1, hr, hl, m2)
                #print("m1",m1,"m2",m2,"ps",ps)
                bak_merkez.append(nVector.yuvarla_vector(rc, nVector.bul_cember_merkezi_3p(m1,ps,m2, duzlem="XYZ")))
                bak_dogru.append(nVector.bul_dogru_uzerindemi_3p(m1,m2,ps))
                #print("Doğruda mı",nVector.bul_dogru_uzerindemi_3p(m1,m2,ps))
            print("\n\n")
            if False not in bak_dogru:                                              # Eğer düz bir doğruysa
                if j == 0:
                    nokta_list.append(m1)
                nokta_list.append(nVector.bul_dogrunun_ortasi_2p(m1, m2))
                nokta_list.append(m2)
            elif bak_merkez[0] == bak_merkez[1] and bak_merkez[1] == bak_merkez[2]:
                if j == 0:
                    nokta_list.append(m1)
                nokta_list.append(nVector.bul_bezier_nokta_4p1t(0.5, m1, hr, hl, m2))
                nokta_list.append(m2)
            else:
                resolution = subcurve.resolution_u
                if resolution % 2 == 1:             # Çözünürlük çift katsayılı yapıldı
                    resolution += 1
                step = 1 / resolution
                for i in range(resolution + 1):
                    o = nVector.bul_bezier_nokta_4p1t(step * i, m1, hr, hl, m2)
                    if i == 0 and j != 0:
                        pass
                    else:
                        nokta_list.append(o)

        #print("nokta list", nokta_list)
        kac_kesit = len(nokta_list) - 2
        for i in range(0, kac_kesit, 2):
            p1 = nokta_list[i]
            p2 = nokta_list[i + 1]
            p3 = nokta_list[i + 2]
            m = nVector.bul_cember_merkezi_3p(p1, p2, p3, duzlem=pref.duzlm)
            b = nVector.bul_yonu_1m3p(m, p1, p2, p3)
            I = m.x - p1.x if pref.duzlm != "G19" else 0
            J = m.y - p1.y if pref.duzlm != "G18" else 0
            K = m.z - p1.z if pref.duzlm != "G17" else 0

            print("p1",p1,"p2",p2,"p3",p3,"m",m, I,J,K)


            limit = 800
            if i == 0:
                self.kodlar.append("G0 Z{1:.{0}f}".format(r,  z_safe))
                self.kodlar.append("G0 X{1:.{0}f} Y{2:.{0}f}".format(r, p1.x, p1.y))
                self.kodlar.append("G1 Z{1:.{0}f} F{2}".format(r,p1.z, pref.hiz_d))


            if abs(I) > limit or abs(J) > limit or abs(K) > limit:
                q = "G1 X{1:.{0}f} Y{2:.{0}f} Z{3:.{0}f}".format(r, p3.x, p3.y, p3.z)
            else:
                q = "{1} X{2:.{0}f} Y{3:.{0}f} Z{4:.{0}f} I{5:.{0}f} J{6:.{0}f} K{7:.{0}f}".format(r, b, p3.x, p3.y, p3.z, I, J, K)
            if i == 0: q += " F{}".format(pref.hiz_f)
            self.kodlar.append(q)
        self.kodlar.append("G0 Z{1:.{0}f}".format(r, z_safe))



    def poly(self, obj, subcurve):
        pref = obj.ncnc_objayar
        r = pref.yvrla_koor
        z_safe = pref.gyuk
        for i, p in enumerate(subcurve.points):
            loc = p.co.to_3d() + obj.location - self.z_adim

            if i == 0:
                self.kodlar.append("G0 Z{1:.{0}f}".format(r, z_safe))
                self.kodlar.append("G0 X{1:.{0}f} Y{2:.{0}f}".format(r, loc.x, loc.y))
                self.kodlar.append("G1 Z{1:.{0}f} F{2}".format(r,loc.z, pref.hiz_d))
            else:
                q = "G1 X{1:.{0}f} Y{2:.{0}f} Z{3:.{0}f}".format(r, loc.x, loc.y, loc.z)
                if i == 1: q += " F{}".format(pref.hiz_f)
                self.kodlar.append(q)

        if subcurve.use_cyclic_u:
            loc = subcurve.points[0].co.to_3d() + obj.location - self.z_adim
            self.kodlar.append("G1 X{1:.{0}f} Y{2:.{0}f} Z{3:.{0}f}".format(r, loc.x, loc.y, loc.z))
            self.kodlar.append("G0 Z{1:.{0}f}".format(r, z_safe))
        else:
            self.kodlar.append("G0 Z{1:.{0}f}".format(r, z_safe))



    def kaydet(self):
        save = bpy.context.scene.ncnc_save
        save.write_update()

        self.file_path = os.path.join(save.dirpath, save.filename + save.uzanti)
        with open(self.file_path, "wb") as f:
            for i in self.kodlar:
                i += "\n"
                f.write(i.encode("ASCII"))





class NCNC_PT_Save(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Output"
    bl_idname = "NCNC_PT_save"

    def draw(self, context):

        save = context.scene.ncnc_save

        layout = self.layout

        tum = layout.column()
        tum.separator()
        row1= tum.column()
        row1.prop(save, 'dirpath', text="")

        row2 = tum.row(align=True)
        row2.scale_x = 0.8
        row2.prop(save, 'filename', text="")
        row2.scale_x = 0.3
        row2.prop(save, 'uzanti', text="")


        tum.separator()
        row4 = tum.row()
        row4.scale_x = 5.2
        row4.label(text="%s" % (os.path.join(save.dirpath,save.filename + save.uzanti)), icon='DISK_DRIVE')
        row4.prop(save, 'write', expand=True)

        row3 = tum.row()
        row3.operator("ncnc.save_ops", text="Dışa Aktar")


        tum.separator()






########################################################################################
########################################################################################
#####   Dahil Objeler


class NCNC_PR_Included_Objs(bpy.types.PropertyGroup):

    def objelist_items(self, context=None):
        objeler = []
        for obj in bpy.data.objects:
            if obj.ncnc_objayar.dahil:
                objeler.append((obj.name, obj.name, ""))
        return objeler

    def objelist_update(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        #bpy.data.objects[self.objelist].select_set(True)
        bpy.ops.object.select_pattern(pattern=self.objelist)
        bpy.context.view_layer.objects.active = bpy.data.objects.get(self.objelist)


    objelist : bpy.props.EnumProperty(items=objelist_items, update=objelist_update)




class NCNC_OT_Included_Objs(bpy.types.Operator):
    bl_idname = "ncnc.included_objs"
    bl_label = "Dahil Objeler Listesi Operatörü"
    bl_description = "Seçilen objeyi ;\n( - ) : Sadece CNC işinden çıkartır.\n(Çöp) : Tamamen objeyi siler"
    bl_options = {'REGISTER'}
    action : bpy.props.EnumProperty(items=[
        ("ekle", "Seçili Objeyi Ekle",""),
        ("cikar", "Seçili Objeyi Çıkart",""),
        ("sil", "Seçili Objeyi Sil", "")
    ])


    def invoke(self, context, event=None):

        props = context.scene.ncnc_iobj

        if self.action == "ekle":
            self.report({'INFO'}, "Obje eklendi : {}".format(props.objelist))
            bpy.data.objects[props.objelist].ncnc_objayar.dahil = True
        elif self.action == "cikar":
            self.report({'INFO'}, "Obje çıkartıldı : {}".format(props.objelist))
            bpy.data.objects[props.objelist].ncnc_objayar.dahil = False
        elif self.action == "sil":
            self.report({'INFO'}, "Obje silindi : {}".format(props.objelist))
            props.objelist_update(context)
            bpy.ops.object.delete(use_global=False, confirm=False)

        return {"FINISHED"}




class NCNC_PT_Included_Objs(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Dahil Objeler"          # Included Objects
    bl_idname = "NCNC_PT_included_objs"
    bl_parent_id = "NCNC_PT_save"

    def draw(self, context):

        layout = self.layout

        props = context.scene.ncnc_iobj

        #layout.use_property_split = True
        #layout.use_property_decorate = False  # No animation.

        row = layout.row()


        col2 = row.column(align=True)
        col2.operator("ncnc.objayar_ops"  , icon="ADD",    text="")
        col2.operator("ncnc.included_objs", icon="REMOVE", text="").action = "cikar"
        col2.operator("ncnc.included_objs", icon="TRASH",  text="").action = "sil"
        col1 = row.column().box()
        col1.prop(props, "objelist", expand=True, emboss=True, )



########################################################################################
########################################################################################
#####   Obje Ayarları



class NCNC_PR_ObjAyar(bpy.types.PropertyGroup):
    """Objenin özellikleri. Objenin kendisi üzerinde bulunur"""

    yvrla_koor : bpy.props.IntProperty(name="Yuvarla (Koordinat)",default=3, min=0, max=6,
                                  description="Koordinatların, ondalık kısmı kaç basamaklı olacak ? (d=3)"
                                              "[0-6] = Kaba Hesap - Detaylı hesap")
    yvrla_cmbr : bpy.props.IntProperty(name="Yuvarla (Çember)",default=1, min=0, max=6,
                                  description="Çembersel hesabın, ondalık kısmı kaç basamaklı olacak ? (d=1). \n"
                                              "[0-6] = Kaba Hesap - Detaylı hesap")
    yvrla_g23d : bpy.props.IntProperty(name="Yuvarla (G2-G3 Koordinat)",default=0, min=0, max=6,
                                  description="G2-G3 koordinatları kaç basamak yuvarlanacak ? (d=0). \n"
                                              "[0-6] = Kaba-Detaylı. GRBL v1.1 için 0 değeri gir")
    cmbr_m_lmt : bpy.props.IntProperty(name="Çember Merkez Uzaklığı Limiti",default=800, min=0, max=6,
                                  description="Eğri hesaplanırken, radyal merkez çok uzakta çıkarsa \n"
                                              "[0-6] = Kaba Hesap - Detaylı hesap")

    duzlm : bpy.props.EnumProperty(items=[("G17", "G17", "XY düzlemini aktif yapar"),
                                          ("G18", "G18", "XZ düzlemini aktif yapar"),
                                          ("G19", "G19", "YZ düzlemini aktif yapar"),
                                          ("XYZ", "XYZ", "Deney aşamasında (GRBL v1.1 ile çalışmıyor)"),

                                          ], name="Düzlem Seçimi", description="Düzlem seçin. default=G17")
    dahil : bpy.props.BoolProperty(name = "İşlenmeye dahil", default=False, description="CNC'de işlensin mi?")
    derin : bpy.props.FloatProperty(default=1, unit="LENGTH",
                                    description="Son işleme derinliği")
    step : bpy.props.FloatProperty(default=0.5, unit="LENGTH",
                                   description="Bir adımda işleme derinliği")
    gyuk : bpy.props.FloatProperty(name="Güvenli Yükseklik", default=5,
                                   description="Başlamadan önce başlangıç noktasının Z yüksekliğine eklenir (d=5)")

    hiz_f : bpy.props.IntProperty(name="İlerleme Hızı (mm/dk)", default=200, min=30,
                                 description="CNC ucu işlem yaparken dakikada kaç mm ilerleyecek (d=200)")
    hiz_d : bpy.props.IntProperty(name="Dalış Hızı (mm/dk)", default=100, min=10,
                                  description="CNC ucu işlem yaparken dakikada kaç mm dalış yapacak. Z'de (d=100)")
    hiz_s : bpy.props.IntProperty( name="Spindle Dönüş Hızı (rpm/dk)", default=1200, min=600,
                                   description="Spindle (kesici uc)'un dönüş hızı. (d=1200)")

    icindeki_tipler : bpy.props.StringProperty()



    def tip_uygun_mu(self, obj):
        """ Obje tipinin, Curve (Bezier veya Poly) olup olmadığını kontrol eder """
        if obj.type == "CURVE":
            o = []
            for i in obj.data.splines:
                o.append(i.type == "POLY" or i.type == "BEZIER")
            return False not in o
        else:
            return False




class NCNC_OT_ObjAyar(bpy.types.Operator):
    bl_idname = "ncnc.objayar_ops"
    bl_label = "Çevir : Curve"
    bl_description = "CNC'de işleyebilmek için Curve'e çevirmek gereklidir"
    bl_options = {'REGISTER'}


    def invoke(self, context, event=None):
        obj = context.active_object
        obj.select_set(True)
        objAyar = obj.ncnc_objayar

        if not obj:
            self.report({'INFO'}, "Seçili obje bulunamadı")
            return {"FINISHED"}

        if obj.type != 'CURVE':                         # Curve değilse
            bpy.ops.object.convert(target='CURVE')      # Curve'e çevir

        if obj.type != 'CURVE':                         # Curve'e çevrilmiyorsa
            self.report({'INFO'},"Curve'e çevrilemez : %s" % (obj.name))
            return {"FINISHED"}                         # Bitir

        if not objAyar.tip_uygun_mu(obj):              # Curve ama Bezier veya Poly değilse    (ilerde geliştirilecek)
            self.report({'INFO'}, "Curve tipi uygun değil : %s" % (obj.name))
            return {"FINISHED"}                         # Bitir


        objAyar.dahil = True                           # Convert edildikten sonra, CNC'de işlenmeye dahil edilir.
        bpy.ops.object.transform_apply(location=False,
                                       rotation=False,
                                       scale=True)      # Scale'ı uygula (Yani 1,1,1 yap)
        if "nCurve" not in obj.name:
            obj.name = "nCurve." + obj.name


        self.report({'INFO'}, "Çevir Curve : %s" % (obj.name))

        return {"FINISHED"}




class NCNC_PT_ObjAyar(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Obje Ayar"
    bl_idname = "NCNC_PT_objayar"

    def draw(self, context):

        obj = context.active_object
        if not obj: return
        objAyar = obj.ncnc_objayar

        layout = self.layout
        row = layout.row(align=True)
        row.prop(obj,"name", text="")
        row.operator("ncnc.objayar_ops", text="", icon="CURVE_DATA")
        r2 = row.row(align=True)
        r2.prop(objAyar, "dahil", text="", icon="CHECKBOX_HLT"  if objAyar.dahil else "CHECKBOX_DEHLT")
        r2.enabled = objAyar.tip_uygun_mu(obj)


        row = layout.row(align=True)
        row.enabled = objAyar.dahil     # Tip uygun değilse buraları pasif yapar
        row.prop(objAyar, "duzlm", expand=True)

        col = layout.column(align=True)
        col.enabled = objAyar.dahil     # Tip uygun değilse buraları pasif yapar
        col.prop(objAyar, "derin", text="Derinlik")
        col.prop(objAyar, "step",  text="Adım")
        col.prop(objAyar, "gyuk")

        col = layout.column(align=True)
        col.enabled = objAyar.dahil  # Tip uygun değilse buraları pasif yapar
        col.prop(objAyar, "hiz_d" )
        col.prop(objAyar, "hiz_f" )
        col.prop(objAyar, "hiz_s" )

        col = layout.column(align=True)
        col.enabled = objAyar.dahil  # Tip uygun değilse buraları pasif yapar
        col.prop(objAyar, "yvrla_cmbr", slider=True)
        col.prop(objAyar, "yvrla_koor", slider=True)


        col = layout.column(align=True)
        col.enabled = objAyar.dahil # Tip uygun değilse buraları pasif yapar
        if obj.type == "CURVE":
            col.prop(obj.data, "resolution_u", slider=True,                text="Resolution Obj General")
            col.prop(obj.data.splines.active, "resolution_u", slider=True, text="Resolution Spline in Obj")








########################################################################################
########################################################################################
########################################################################################



"""
    Header -> _HT_
    Menu -> _MT_
    Operator -> _OT_
    Panel -> _PT_
    UIList -> _UL_
"""


classes = [NCNC_PR_ObjAyar, NCNC_OT_ObjAyar, NCNC_PT_ObjAyar,
           NCNC_PR_Save, NCNC_OT_Save, NCNC_PT_Save,
           NCNC_PR_Included_Objs, NCNC_OT_Included_Objs, NCNC_PT_Included_Objs,
           NCNC_PR_Props,
           NCNC_OT_Tools,
           NCNC_PT_Tools, NCNC_PT_Malzeme]


def register():
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.Object.ncnc_objayar =bpy.props.PointerProperty(type=NCNC_PR_ObjAyar)
    bpy.types.Scene.ncnc_props =bpy.props.PointerProperty(type=NCNC_PR_Props)
    bpy.types.Scene.ncnc_save =bpy.props.PointerProperty(type=NCNC_PR_Save)
    bpy.types.Scene.ncnc_iobj =bpy.props.PointerProperty(type=NCNC_PR_Included_Objs)

def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)

    del bpy.types.Scene.ncnc_iobj
    del bpy.types.Scene.ncnc_props
    del bpy.types.Scene.ncnc_save
    del bpy.types.Object.ncnc_objayar

if __name__ == "__main__":
    register()
